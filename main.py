"""
AstrBot Platform Parser Plugin
视频解析API插件
"""

import requests
import json
import re
import logging
from urllib.parse import urlparse

# 设置日志
logger = logging.getLogger(__name__)

# 尝试不同的导入路径
try:
    from astrbot.api.star import Context, Star, register
    from astrbot.api.event import filter
    # 不导入 AstrBotEvent，使用通用类型
    USE_STAR_API = True
except ImportError:
    try:
        from astrbot.plugin import Plugin, on_message
        from astrbot.event import MessageEvent
        from astrbot.context import Context
        USE_STAR_API = False
    except ImportError:
        # 最基础的导入方式
        import logging
        logger = logging.getLogger(__name__)
        USE_STAR_API = False

if USE_STAR_API:
    @register("platform_hx", "视频解析API插件", "解析部分平台API的插件", "1.0.0")
    class PlatformParser(Star):
        
        def __init__(self, context: Context):
            self.context = context
            self.api_base_url = "http://119.45.171.58:10010"
            logger.info("PlatformParser 插件初始化完成")
            
        @filter.command("parse", "解析视频链接")
        async def parse_command(self, event):
            """解析视频链接"""
            # 获取命令参数 - 兼容不同的事件对象
            message_text = self._get_message_text(event)
            parts = message_text.split(maxsplit=1)
            
            if len(parts) < 2:
                await self._send_message(event, "❌ 请提供视频链接\n用法：/parse <视频URL>")
                return
                
            video_url = parts[1].strip()
            
            # 验证URL格式
            try:
                parsed_url = urlparse(video_url)
                if not all([parsed_url.scheme, parsed_url.netloc]):
                    raise ValueError("Invalid URL")
            except ValueError:
                await self._send_message(event, "❌ 无效的URL格式")
                return
                
            await self._send_message(event, "🔄 正在解析视频...")
            
            try:
                response = requests.post(
                    f"{self.api_base_url}/parse",
                    json={"url": video_url},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result_str = json.dumps(result, indent=2, ensure_ascii=False)
                    await self._send_message(event, f"✅ 解析成功！\n```json\n{result_str}\n```")
                else:
                    await self._send_message(event, f"❌ 解析失败：HTTP {response.status_code}\n{response.text}")
                    
            except requests.exceptions.Timeout:
                await self._send_message(event, "❌ 请求超时，请稍后重试")
            except requests.exceptions.ConnectionError:
                await self._send_message(event, "❌ 无法连接到解析服务")
            except Exception as e:
                await self._send_message(event, f"❌ 解析出错：{str(e)}")
        
        @filter.command("api_status", "检查API服务状态")
        async def api_status_command(self, event):
            """检查API服务状态"""
            try:
                response = requests.get(f"{self.api_base_url}/openapi.json", timeout=10)
                if response.status_code == 200:
                    await self._send_message(event, "✅ 解析API服务正常")
                else:
                    await self._send_message(event, f"⚠️ API服务响应异常：HTTP {response.status_code}")
            except Exception as e:
                await self._send_message(event, f"❌ 无法连接到API服务：{str(e)}")
        
        @filter.command("help_parse", "解析插件帮助")
        async def help_command(self, event):
            """显示帮助信息"""
            help_text = """
🎥 视频解析插件帮助

命令：
• /parse <视频URL> - 解析视频链接
• /api_status - 检查API服务状态  
• /help_parse - 显示此帮助信息
• /sphe - 快速显示插件帮助

支持的平台：所有平台
API地址：http://119.45.171.58:10010
            """
            await self._send_message(event, help_text.strip())
        
        @filter.command("sphe", "快速帮助")
        async def sphe_command(self, event):
            """快速显示插件帮助"""
            logger.info("收到 sphe 命令")
            help_text = """
🎥 视频解析插件

▪️ /parse <视频URL> - 解析视频
▪️ /api_status - API状态
▪️ /help_parse - 详细帮助
▪️ /sphe - 快速帮助

📍 API: http://119.45.171.58:10010
            """
            await self._send_message(event, help_text.strip())
            logger.info("sphe 命令处理完成")
        
        def _get_message_text(self, event):
            """获取消息文本的兼容方法"""
            # 尝试多种可能的属性名
            for attr in ['message_str', 'content', 'text', 'message', 'raw_message']:
                if hasattr(event, attr):
                    value = getattr(event, attr)
                    if hasattr(value, 'strip'):  # 确保是字符串
                        return value.strip()
                    elif hasattr(value, 'text'):  # 如果是消息对象
                        return value.text.strip()
            return ""
        
        def _get_session_type(self, event):
            """获取会话类型（私聊/群聊）"""
            # 尝试多种可能的属性名
            if hasattr(event, 'session_type'):
                return event.session_type
            elif hasattr(event, 'detail_type'):
                return event.detail_type
            elif hasattr(event, 'message_type'):
                return event.message_type
            elif hasattr(event, 'ctx') and isinstance(event.ctx, dict):
                return event.ctx.get('session_type') or event.ctx.get('detail_type') or event.ctx.get('message_type')
            return 'unknown'
        
        def _strip_command_prefix(self, text):
            """移除命令前缀"""
            prefixes = ['/', '!', '.', '~']
            for prefix in prefixes:
                if text.startswith(prefix):
                    return text[len(prefix):]
            return text
        
        async def _send_message(self, event, message):
            """发送消息的兼容方法"""
            try:
                # 尝试多种可能的发送方法
                logger.info(f"尝试发送消息: {message[:50]}...")
                if hasattr(event, 'send'):
                    logger.info("使用 event.send 方法")
                    await event.send(message)
                elif hasattr(event, 'reply'):
                    logger.info("使用 event.reply 方法")
                    await event.reply(message)
                elif hasattr(event, 'message') and hasattr(event.message, 'reply'):
                    logger.info("使用 event.message.reply 方法")
                    await event.message.reply(message)
                elif hasattr(self.context, 'send_message'):
                    logger.info("使用 context.send_message 方法")
                    await self.context.send_message(message)
                else:
                    logger.warning("无法找到发送消息的方法")
                    print(f"无法发送消息: {message}")
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                print(f"发送消息失败: {e}")
        
        # 添加一个通用的消息处理器来调试
        @filter.command("test", "测试命令")
        async def test_command(self, event):
            """测试命令是否工作"""
            session_type = self._get_session_type(event)
            logger.info(f"收到 test 命令，会话类型: {session_type}")
            await self._send_message(event, f"✅ 插件工作正常！会话类型: {session_type}")
            logger.info("test 命令处理完成")
        
        # 添加一个通用的消息处理器来处理无前缀命令（主要用于私聊）
        # 注意：这个装饰器可能不存在，先注释掉，如果需要可以尝试其他方式
        # @filter.message()
        async def handle_message(self, event):
            """处理普通消息，支持无前缀命令"""
            message_text = self._get_message_text(event)
            session_type = self._get_session_type(event)
            
            logger.info(f"收到消息: {message_text}, 会话类型: {session_type}")
            
            # 在私聊中支持无前缀命令
            if session_type in ['private', 'friend']:
                clean_text = self._strip_command_prefix(message_text.strip())
                
                # 检查是否是我们的命令
                if clean_text == 'test' or clean_text == 'sphe':
                    logger.info(f"私聊无前缀命令: {clean_text}")
                    if clean_text == 'test':
                        await self._send_message(event, "✅ 插件工作正常！私聊无前缀命令测试成功！")
                    elif clean_text == 'sphe':
                        help_text = """
🎥 视频解析插件（私聊模式）

▪️ test 或 /test - 测试插件
▪️ sphe 或 /sphe - 快速帮助
▪️ /parse <URL> - 解析视频
▪️ /api_status - API状态

📍 API: http://119.45.171.58:10010
                        """
                        await self._send_message(event, help_text.strip())
                    return
            
            # 在群聊中，也可以尝试处理无前缀命令（可选）
            elif session_type in ['group', 'supergroup']:
                clean_text = self._strip_command_prefix(message_text.strip())
                if clean_text == 'sphe':
                    logger.info("群聊无前缀 sphe 命令")
                    help_text = """
🎥 视频解析插件

▪️ /parse <URL> - 解析视频
▪️ /api_status - API状态  
▪️ /sphe - 快速帮助

📍 API: http://119.45.171.58:10010
                    """
                    await self._send_message(event, help_text.strip())
                    return

else:
    # 使用Plugin类的方式
    class PlatformParser(Plugin):
        """视频解析API插件"""
        
        def __init__(self):
            super().__init__()
            self.api_base_url = "http://119.45.171.58:10010"
        
        @on_message()
        async def handle_message(self, event):
            """处理消息事件"""
            content = event.content.strip()
            
            if content.startswith('/parse '):
                video_url = content[7:].strip()
                if not video_url:
                    await event.reply("❌ 请提供视频链接\n用法：/parse <视频URL>")
                    return
                    
                # 验证URL格式
                try:
                    parsed_url = urlparse(video_url)
                    if not all([parsed_url.scheme, parsed_url.netloc]):
                        raise ValueError("Invalid URL")
                except ValueError:
                    await event.reply("❌ 无效的URL格式")
                    return
                    
                await event.reply("🔄 正在解析视频...")
                
                try:
                    response = requests.post(
                        f"{self.api_base_url}/parse",
                        json={"url": video_url},
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        result_str = json.dumps(result, indent=2, ensure_ascii=False)
                        await event.reply(f"✅ 解析成功！\n```json\n{result_str}\n```")
                    else:
                        await event.reply(f"❌ 解析失败：HTTP {response.status_code}\n{response.text}")
                        
                except requests.exceptions.Timeout:
                    await event.reply("❌ 请求超时，请稍后重试")
                except requests.exceptions.ConnectionError:
                    await event.reply("❌ 无法连接到解析服务")
                except Exception as e:
                    await event.reply(f"❌ 解析出错：{str(e)}")
            
            elif content == '/api_status':
                try:
                    response = requests.get(f"{self.api_base_url}/openapi.json", timeout=10)
                    if response.status_code == 200:
                        await event.reply("✅ 解析API服务正常")
                    else:
                        await event.reply(f"⚠️ API服务响应异常：HTTP {response.status_code}")
                except Exception as e:
                    await event.reply(f"❌ 无法连接到API服务：{str(e)}")
            
            elif content == '/help_parse':
                help_text = """
🎥 视频解析插件帮助

命令：
• /parse <视频URL> - 解析视频链接
• /api_status - 检查API服务状态  
• /help_parse - 显示此帮助信息
• /sphe - 快速显示插件帮助

支持的平台：所有平台
API地址：http://119.45.171.58:10010
                """
                await event.reply(help_text.strip())
            
            elif content == '/sphe':
                help_text = """
🎥 视频解析插件

▪️ /parse <视频URL> - 解析视频
▪️ /api_status - API状态
▪️ /help_parse - 详细帮助
▪️ /sphe - 快速帮助

📍 API: http://119.45.171.58:10010
                """
                await event.reply(help_text.strip())