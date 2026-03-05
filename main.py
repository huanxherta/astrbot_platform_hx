"""
AstrBot Platform Parser Plugin
视频解析API插件
"""

import requests
import json
import re
import os
from urllib.parse import urlparse
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

# 版本号获取函数
# 插件版本信息由 metadata.yaml 提供，一般由开发者手动维护。
# 框架在加载时会读取该字段，插件运行时修改文件不会影响当前加载的版本，
# 因此不推荐在代码中做自动变更（见：https://docs.astrbot.app/dev/star/plugin-new.html）。
def get_version():
    """从 metadata.yaml 中读取版本号"""
    metadata_path = os.path.join(os.path.dirname(__file__), 'metadata.yaml')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('version:'):
                    return line.split(':')[1].strip().strip('"')
    except Exception:
        pass
    return "1.0.0"

# NOTE: 不再在插件加载时自动修改 version，避免与框架读写时机冲突。

@register("platform_hx", "hx", "解析部分平台API的插件", get_version())
class PlatformParser(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_base_url = "http://localhost:10010"  # 使用本地API服务器
        logger.info(f"PlatformParser 插件初始化完成，版本: {get_version()}")

    async def initialize(self):
        """插件异步初始化方法"""
        logger.info("PlatformParser 插件启动完成")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def auto_parse_video(self, event: AstrMessageEvent):
        """自动检测消息中的视频链接并解析（模糊匹配链接）"""
        message_str = event.message_str.strip()
        
        # 检测是否包含支持的视频链接
        supported_domains = ['tiktok.com', 'douyin.com', 'youtube.com', 'youtu.be', 'vimeo.com', 'instagram.com', 'twitter.com', 'x.com']
        video_url = None
        
        # 从消息中提取 URL（模糊匹配）
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message_str)
        
        for url in urls:
            if any(domain in url for domain in supported_domains):
                video_url = url
                logger.info(f"[auto_parse_video] 检测到视频链接: {url}")
                break
        
        if not video_url:
            # 没有检测到视频链接，跳过处理
            return
        
        # 验证URL格式
        try:
            parsed_url = urlparse(video_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid URL")
        except ValueError:
            return event.plain_result("❌ 无效的URL格式")
            
        # 请求解析接口
        try:
            logger.info(f"开始解析视频: {video_url}")
            response = requests.post(
                f"{self.api_base_url}/parse",
                json={"url": video_url},
                headers={"Content-Type": "application/json"},
                timeout=180
            )
            logger.info(f"API响应状态: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"API错误: HTTP {response.status_code}, 响应: {response.text}")
                return event.plain_result(f"❌ 解析失败：HTTP {response.status_code}\n{response.text}")

            result = response.json()
            logger.info(f"解析结果: {result}")
            title = result.get("title", "Unknown Video")

            # 尝试下载并发送文件（兼容各平台的 MessageChain）
            file_sent = False
            try:
                resp = requests.get(
                    f"{self.api_base_url}/download",
                    params={"url": video_url},
                    stream=True,
                    timeout=180,
                )
                if resp.status_code == 200:
                    # 保存到当前工作目录，保持原始文件名如果提供
                    filename = "video.mp4"
                    cd = resp.headers.get("content-disposition", "")
                    m = re.search(r'filename\"?(.+?)\"?($|;)', cd)
                    if m:
                        filename = m.group(1)
                    temp_path = os.path.join(os.getcwd(), filename)
                    with open(temp_path, "wb") as f:
                        for chunk in resp.iter_content(8192):
                            if chunk:
                                f.write(chunk)

                    # 构造 MessageChain 包含标题和视频，使用 Video 组件让平台正确识别
                    from astrbot.api.message_components import Video
                    from astrbot.api.message_components import Plain
                    from astrbot.api.event import MessageChain

                    chain = MessageChain()
                    chain.chain.append(Plain(text=f"📹 {title}"))
                    chain.chain.append(Video.fromFileSystem(temp_path))
                    await event.send(chain)
                    file_sent = True
                else:
                    logger.warning(f"下载接口返回 {resp.status_code}, 未发送文件")
            except Exception as e:
                logger.warning(f"下载阶段失败: {e}")

            if file_sent:
                # 文件已发送，不再返回其他消息
                return
            else:
                # 如果下载/发送失败，显示标题和错误提示
                logger.warning(f"无法发送视频文件，仅显示标题: {title}")
                return event.plain_result(f"📹 {title}\n\n⚠️ 视频下载失败，请稍后重试")

        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            return event.plain_result("❌ 请求超时，请稍后重试")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {str(e)}")
            return event.plain_result("❌ 无法连接到解析服务")
        except Exception as e:
            logger.error(f"解析异常: {str(e)}", exc_info=True)
            return event.plain_result(f"❌ 解析出错：{str(e)}")
    
    
    
    @filter.command("api_status")
    async def api_status_command(self, event: AstrMessageEvent):
        """检查解析API服务状态"""
        try:
            logger.info("检查API服务状态...")
            response = requests.get(f"{self.api_base_url}/openapi.json", timeout=5)
            if response.status_code == 200:
                logger.info("API服务正常")
                return event.plain_result("✅ 解析API服务正常")
            else:
                logger.error(f"API服务异常: HTTP {response.status_code}")
                return event.plain_result(f"⚠️ API服务响应异常：HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"API连接失败: {str(e)}")
            return event.plain_result(f"❌ 无法连接到API服务：{str(e)}")
    
    @filter.command("ping_api")
    async def ping_api_command(self, event: AstrMessageEvent):
        """测试API连接"""
        try:
            logger.info("测试API连接...")
            response = requests.get(f"{self.api_base_url}/", timeout=3)
            if response.status_code in [200, 404]:  # 404也表示服务器可达
                logger.info("API服务器可达")
                return event.plain_result("✅ API服务器连接正常")
            else:
                logger.error(f"API服务器异常: HTTP {response.status_code}")
                return event.plain_result(f"⚠️ API服务器异常：HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"API连接测试失败: {str(e)}")
            return event.plain_result(f"❌ 无法连接到API服务器：{str(e)}")
    
    @filter.command("help")
    async def help_command(self, event: AstrMessageEvent):
        """显示详细帮助信息"""
        help_text = f"""
🎥 视频解析插件帮助 (v{get_version()})

用法：
• 直接发送视频链接 - 自动解析并发送
  支持：TikTok、抖音、YouTube、Vimeo、Instagram

命令：
• /help - 显示此帮助信息
• /sphe - 快速帮助
• /test - 测试插件状态
• /api_status - 检查API服务状态  
• /ping_api - 测试API连接

API地址：http://localhost:10010 (本地服务器)
版本: {get_version()}
        """
        return event.plain_result(help_text.strip())
    
    @filter.command("sphe")
    async def sphe_command(self, event: AstrMessageEvent):
        """快速显示插件帮助"""
        logger.info("收到 sphe 命令")
        help_text = f"""
🎥 视频解析插件 v{get_version()}

用法：直接发送视频链接，自动解析
支持：TikTok、抖音、YouTube、Vimeo、Instagram

▪️ /help - 详细帮助
▪️ /test - 测试插件
▪️ /api_status - API状态
▪️ /ping_api - 测试连接

📍 API: http://localhost:10010 (本地服务器)
        """
        return event.plain_result(help_text.strip())

    @filter.command("test")
    async def test_command(self, event: AstrMessageEvent):
        """测试插件状态"""
        user_name = event.get_sender_name()
        logger.info(f"收到 test 命令，来自用户: {user_name}")
        return event.plain_result(f"✅ 插件工作正常！\n👋 你好 {user_name}\n📊 当前版本: {get_version()}")

    async def terminate(self):
        """插件销毁方法"""
        logger.info("PlatformParser 插件已停止")