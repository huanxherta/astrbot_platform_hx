"""
AstrBot Platform Parser Plugin
视频解析API插件
"""

import requests
import json
from urllib.parse import urlparse
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter
from astrbot.api.platform import AstrBotEvent, Platform

@register("platform_hx", "视频解析API插件")
class PlatformParser(Star):
    
    def __init__(self, context: Context):
        self.context = context
        self.api_base_url = "http://119.45.171.58:10010"
        
    @filter.command("parse", "解析视频链接")
    async def parse_command(self, event: AstrBotEvent):
        """
        解析视频链接
        用法：/parse <视频URL>
        """
        # 获取命令参数
        message_text = event.message_str.strip()
        parts = message_text.split(maxsplit=1)
        
        if len(parts) < 2:
            await event.send("❌ 请提供视频链接\n用法：/parse <视频URL>")
            return
            
        video_url = parts[1].strip()
        
        # 验证URL格式
        try:
            parsed_url = urlparse(video_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid URL")
        except ValueError:
            await event.send("❌ 无效的URL格式")
            return
            
        await event.send("🔄 正在解析视频...")
        
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
                await event.send(f"✅ 解析成功！\n```json\n{result_str}\n```")
            else:
                await event.send(f"❌ 解析失败：HTTP {response.status_code}\n{response.text}")
                
        except requests.exceptions.Timeout:
            await event.send("❌ 请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            await event.send("❌ 无法连接到解析服务")
        except Exception as e:
            await event.send(f"❌ 解析出错：{str(e)}")
    
    @filter.command("api_status", "检查API服务状态")
    async def api_status_command(self, event: AstrBotEvent):
        """
        检查解析API服务状态
        """
        try:
            response = requests.get(f"{self.api_base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                await event.send("✅ 解析API服务正常")
            else:
                await event.send(f"⚠️ API服务响应异常：HTTP {response.status_code}")
        except Exception as e:
            await event.send(f"❌ 无法连接到API服务：{str(e)}")
    
    @filter.command("help_parse", "解析插件帮助")
    async def help_command(self, event: AstrBotEvent):
        """
        显示插件帮助信息
        """
        help_text = """
🎥 视频解析插件帮助

命令：
• /parse <视频URL> - 解析视频链接
• /api_status - 检查API服务状态  
• /help_parse - 显示此帮助信息

支持的平台：所有平台
API地址：http://119.45.171.58:10010
        """
        await event.send(help_text.strip())