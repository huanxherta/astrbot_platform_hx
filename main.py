"""
AstrBot Platform Parser Plugin
视频解析API插件
"""

import requests
import json
import re
from urllib.parse import urlparse

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
            help_text = """
🎥 视频解析插件

▪️ /parse <视频URL> - 解析视频
▪️ /api_status - API状态
▪️ /help_parse - 详细帮助
▪️ /sphe - 快速帮助

📍 API: http://119.45.171.58:10010
            """
            await self._send_message(event, help_text.strip())
        
        def _get_message_text(self, event):
            """获取消息文本的兼容方法"""
            # 尝试多种可能的属性名
            for attr in ['message_str', 'content', 'text', 'message']:
                if hasattr(event, attr):
                    value = getattr(event, attr)
                    if hasattr(value, 'strip'):  # 确保是字符串
                        return value.strip()
                    elif hasattr(value, 'text'):  # 如果是消息对象
                        return value.text.strip()
            return ""
        
        async def _send_message(self, event, message):
            """发送消息的兼容方法"""
            try:
                # 尝试多种可能的发送方法
                if hasattr(event, 'send'):
                    await event.send(message)
                elif hasattr(event, 'reply'):
                    await event.reply(message)
                elif hasattr(event, 'message') and hasattr(event.message, 'reply'):
                    await event.message.reply(message)
                elif hasattr(self.context, 'send_message'):
                    await self.context.send_message(message)
                else:
                    print(f"无法发送消息: {message}")
            except Exception as e:
                print(f"发送消息失败: {e}")

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