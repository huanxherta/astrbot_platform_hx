"""
AstrBot Platform Parser Plugin
视频解析API插件
"""

import requests
import json
import re
from urllib.parse import urlparse
from astral.plugins import Plugin
from astral.models import Message, Event

class PlatformParser(Plugin):
    """视频解析API插件"""
    
    name = "astrbot_platform_hx"
    version = "1.0.0"
    description = "解析部分平台API的插件"
    
    def __init__(self):
        super().__init__()
        self.api_base_url = "http://119.45.171.58:10010"
    
    async def on_load(self):
        """插件加载时运行一次"""
        self.logger.info(f"{self.name} v{self.version} 加载完成")
    
    @Plugin.on_message()
    async def handle_message(self, event: Message):
        """处理消息事件"""
        content = event.content.strip()
        
        # 处理 /parse 命令
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
                # 调用解析API
                response = requests.post(
                    f"{self.api_base_url}/parse",
                    json={"url": video_url},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # 格式化响应结果
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
        
        # 处理 /api_status 命令
        elif content == '/api_status':
            try:
                response = requests.get(f"{self.api_base_url}/openapi.json", timeout=10)
                if response.status_code == 200:
                    await event.reply("✅ 解析API服务正常")
                else:
                    await event.reply(f"⚠️ API服务响应异常：HTTP {response.status_code}")
            except Exception as e:
                await event.reply(f"❌ 无法连接到API服务：{str(e)}")
        
        # 处理 /help_parse 命令
        elif content == '/help_parse':
            help_text = """
🎥 视频解析插件帮助

命令：
• /parse <视频URL> - 解析视频链接
• /api_status - 检查API服务状态  
• /help_parse - 显示此帮助信息

支持的平台：所有平台
API地址：http://119.45.171.58:10010
            """
            await event.reply(help_text.strip())