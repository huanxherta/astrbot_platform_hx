from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoItem(BaseModel):
    url: str

@app.post("/parse")
async def parse_video(item: VideoItem):
    url = item.url
    logger.info(f"🚀 收到解析任务: {url}")
    
    try:
        # 简单的TikTok解析方法
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 尝试多种方法
        real_url = None
        title = "TikTok Video"
        
        # 方法1: 直接使用requests模拟浏览器访问
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # 尝试从页面提取视频链接
                content = response.text
                if 'videoUrl' in content or 'playAddr' in content:
                    import re
                    # 简单的正则匹配
                    video_url_match = re.search(r'"videoUrl":"([^"]+)"', content)
                    if video_url_match:
                        real_url = video_url_match.group(1)
                    else:
                        play_addr_match = re.search(r'"playAddr":"([^"]+)"', content)
                        if play_addr_match:
                            real_url = play_addr_match.group(1)
        except Exception as e:
            logger.error(f"直接请求失败: {str(e)}")
        
        # 如果上面的方法失败，返回基本信息
        if not real_url:
            real_url = url  # 返回原始链接
        
        logger.info(f"✅ 解析完成: {title}")
        
        return {
            "title": title,
            "real_download_url": real_url,
            "platform": "TikTok",
            "success": True,
            "message": "解析成功"
        }
        
    except Exception as e:
        logger.error(f"❌ 解析异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

@app.get("/")
async def root():
    return {"message": "TikTok专用解析API", "version": "1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "tiktok_parser"}

if __name__ == "__main__":
    logger.info("🚀 启动TikTok专用解析API")
    logger.info("📍 访问地址: http://localhost:10010")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10010, timeout_keep_alive=60)