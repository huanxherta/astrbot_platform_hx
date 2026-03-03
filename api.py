from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import uvicorn
import logging
import os

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
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extract_flat': False,
            'ignoreerrors': True,
        }

        # 检测平台
        if 'tiktok.com' in url or 'douyin.com' in url:
            logger.info("📱 检测到TikTok/抖音链接")
            ydl_opts['extractor_args'] = {
                'tiktok': {'api_url': 'https://api16-normal-useast5a.tiktokv.com'}
            }
        elif 'youtube.com' in url or 'youtu.be' in url:
            logger.info("📺 检测到YouTube链接")
            cookie_path = "www.youtube.com_cookies.txt"
            if os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path
                logger.info(f"🍪 加载Cookie: {cookie_path}")
            else:
                logger.warning("⚠️ 未找到Cookie文件，匿名解析")
        else:
            logger.info("🌐 其他平台链接")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                logger.error(f"提取信息失败: {str(e)}")
                info = ydl.extract_info(url, download=False, process=False)

            if not info:
                raise HTTPException(status_code=400, detail="无法获取视频信息")

            title = info.get('title', 'Unknown Video')
            real_url = None

            # 从formats中查找最佳链接
            formats = info.get('formats', [])
            if formats:
                for fmt in sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True):
                    if fmt.get('url') and fmt.get('vcodec') != 'none' and 'm3u8' not in fmt.get('url', ''):
                        real_url = fmt['url']
                        break

            if not real_url:
                real_url = info.get('webpage_url', info.get('url', ''))

            platform = "TikTok" if "tiktok.com" in url else "YouTube" if "youtube.com" in url else "Unknown"
            logger.info(f"✅ 解析成功: {title}")

            return {
                "title": title,
                "real_download_url": real_url,
                "platform": platform,
                "duration": info.get('duration'),
                "view_count": info.get('view_count'),
                "uploader": info.get('uploader'),
            }

    except Exception as e:
        logger.error(f"❌ 解析异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "视频解析API服务运行中", "endpoints": {"parse": "POST /parse"}}

@app.get("/status")
async def status():
    return {"status": "healthy", "service": "video_parser"}

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

if __name__ == "__main__":
    logger.info("🚀 启动视频解析API服务器")
    logger.info("📍 访问地址: http://localhost:10010")
    logger.info("📖 API文档: http://localhost:10010/docs")
    uvicorn.run(app, host="0.0.0.0", port=10010, timeout_keep_alive=60)
