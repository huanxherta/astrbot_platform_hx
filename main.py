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

# 自动读取和更新版本号
def get_version():
    """获取当前版本号"""
    metadata_path = os.path.join(os.path.dirname(__file__), 'metadata.yaml')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('version:'):
                    return line.split(':')[1].strip().strip('"')
    except:
        pass
    return "1.0.0"

def increment_version():
    """版本号自动增加0.01"""
    metadata_path = os.path.join(os.path.dirname(__file__), 'metadata.yaml')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('version:'):
                current_version = line.split(':')[1].strip().strip('"')
                try:
                    version_float = float(current_version)
                    new_version = f"{version_float + 0.01:.2f}"
                    new_line = f'version: "{new_version}"'
                    new_lines.append(new_line)
                    logger.info(f"版本号从 {current_version} 更新到 {new_version}")
                except:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
    except Exception as e:
        logger.error(f"更新版本号失败: {e}")

# 每次插件加载时自动更新版本号
increment_version()

@register("platform_hx", "hx", "解析部分平台API的插件", get_version())
class PlatformParser(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_base_url = "http://localhost:10010"  # 使用本地API服务器
        logger.info(f"PlatformParser 插件初始化完成，版本: {get_version()}")

    async def initialize(self):
        """插件异步初始化方法"""
        logger.info("PlatformParser 插件启动完成")

    @filter.command("parse")
    async def parse_command(self, event: AstrMessageEvent):
        """解析视频链接"""
        message_str = event.message_str
        parts = message_str.split(maxsplit=1)
        
        if len(parts) < 2:
            return event.plain_result("❌ 请提供视频链接\n用法：/parse <视频URL>")
            
        video_url = parts[1].strip()
        
        # 验证URL格式
        try:
            parsed_url = urlparse(video_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid URL")
        except ValueError:
            return event.plain_result("❌ 无效的URL格式")
            
        return event.plain_result("🔄 正在解析视频...")
        
        try:
            logger.info(f"开始解析视频: {video_url}")
            response = requests.post(
                f"{self.api_base_url}/parse",
                json={"url": video_url},
                headers={"Content-Type": "application/json"},
                timeout=5  # 进一步减少超时时间
            )
            logger.info(f"API响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"解析结果: {result}")
                result_str = json.dumps(result, indent=2, ensure_ascii=False)
                return event.plain_result(f"✅ 解析成功！\n```json\n{result_str}\n```")
            else:
                logger.error(f"API错误: HTTP {response.status_code}, 响应: {response.text}")
                return event.plain_result(f"❌ 解析失败：HTTP {response.status_code}\n{response.text}")
                
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
    
    @filter.command("help_parse")
    async def help_command(self, event: AstrMessageEvent):
        """显示详细帮助信息"""
        help_text = f"""
🎥 视频解析插件帮助 (v{get_version()})

命令：
• /parse <视频URL> - 解析视频链接
• /api_status - 检查API服务状态  
• /ping_api - 测试API连接
• /help_parse - 显示此帮助信息
• /sphe - 快速显示插件帮助
• /test - 测试插件状态

支持的平台：所有平台
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

▪️ /parse <视频URL> - 解析视频
▪️ /api_status - API状态
▪️ /ping_api - 测试API连接
▪️ /help_parse - 详细帮助
▪️ /sphe - 快速帮助
▪️ /test - 测试插件

📍 API: http://localhost:10010 (本地服务器)
        """
        return event.plain_result(help_text.strip())
        logger.info("sphe 命令处理完成")

    @filter.command("test")
    async def test_command(self, event: AstrMessageEvent):
        """测试插件状态"""
        user_name = event.get_sender_name()
        logger.info(f"收到 test 命令，来自用户: {user_name}")
        return event.plain_result(f"✅ 插件工作正常！\n👋 你好 {user_name}\n📊 当前版本: {get_version()}")
        logger.info("test 命令处理完成")

    async def terminate(self):
        """插件销毁方法"""
        logger.info("PlatformParser 插件已停止")