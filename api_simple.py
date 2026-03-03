from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import uvicorn
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
        # 使用最简化配置
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取信息
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise HTTPException(status_code=400, detail="无法获取视频信息")
            
            # 获取基本信息
            title = info.get('title', 'Unknown Video')
            
            # 多种方法尝试获取下载链接
            real_url = None
            
            # 方法1: 直接URL
            if info.get('url'):
                real_url = info.get('url')
            
            # 方法2: 从formats获取
            if not real_url and info.get('formats'):
                for fmt in info.get('formats', []):
                    if fmt.get('url') and not fmt.get('url', '').endswith('.m3u8'):
                        real_url = fmt['url']
                        break
            
            # 方法3: 网页URL
            if not real_url:
                real_url = info.get('webpage_url')
            
            # 判断平台
            platform = "TikTok" if "tiktok.com" in url else "YouTube" if "youtube.com" in url else "Unknown"
            
            logger.info(f"✅ 解析成功: {title}")
            
            return {
                "title": title,
                "real_download_url": real_url,
                "platform": platform,
                "success": real_url is not None,
                "message": f"成功解析{platform}视频" if real_url else "解析失败"
            }
            
    except Exception as e:
        logger.error(f"❌ 解析异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

@app.get("/")
async def root():
    return {"message": "视频解析API服务运行中", "version": "2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "video_parser"}

if __name__ == "__main__":
    logger.info("🚀 启动视频解析API服务器 v2.0")
    logger.info("📍 访问地址: http://localhost:10010")
    uvicorn.run(app, host="0.0.0.0", port=10010, timeout_keep_alive=60)