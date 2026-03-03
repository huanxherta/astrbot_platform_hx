from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import uvicorn
import logging
import os
import requests

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
        # 创建 yt-dlp 选项，支持多平台
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # 获取最佳质量的MP4
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,  # 跳过证书验证
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extract_flat': False,  # 不分离播放列表
            'ignoreerrors': True,  # 忽略错误继续
        }

        # 检测平台并添加特定选项
        if 'tiktok.com' in url or 'douyin.com' in url:
            logger.info("📱 检测到TikTok/抖音链接")
            # TikTok 特殊配置
            ydl_opts.update({
                'extractor_args': {
                    'tiktok': {
                        'api_url': 'https://api16-normal-useast5a.tiktokv.com',
                    }
                }
            })
        elif 'youtube.com' in url or 'youtu.be' in url:
            logger.info("📺 检测到YouTube链接")
            # YouTube Cookie配置
            cookie_path = "www.youtube.com_cookies.txt"
            if os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path
                logger.info(f"🍪 成功加载 Cookie 文件: {cookie_path}")
            else:
                logger.warning("⚠️ 未找到 Cookie 文件，将尝试匿名解析")
        else:
            logger.info("🌐 检测到其他平台链接")
            # 通用配置
            ydl_opts.update({
                'nocheckcertificate': True,
                'ignoreerrors': True,
            })
        elif 'youtube.com' in url or 'youtu.be' in url:
            logger.info("📺 检测到YouTube链接")
            # YouTube Cookie配置
            cookie_path = "www.youtube.com_cookies.txt"
            if os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path
                logger.info(f"🍪 成功加载 Cookie 文件: {cookie_path}")
            else:
                logger.warning("⚠️ 未找到 Cookie 文件，将尝试匿名解析")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 获取视频信息
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                logger.error(f"提取信息失败: {str(e)}")
                # 尝试简单的提取方式
                info = ydl.extract_info(url, download=False, process=False)
            
            # 检查info是否有效
            if not info:
                logger.error("无法获取视频信息")
                raise HTTPException(status_code=400, detail="无法获取视频信息")
            
            # 初始化变量
            real_url = None
            title = info.get('title', 'Unknown Video')
            
            # 查找最佳格式
            formats = info.get('formats', [])
            if formats:
                # 按质量排序，优先选择非m3u8的格式
                for fmt in sorted(formats, key=lambda x: x.get('height', 0), reverse=True):
                    if fmt.get('url') and fmt.get('vcodec') != 'none' and 'm3u8' not in fmt.get('url', ''):
                        real_url = fmt['url']
                        break
            
            # 如果没找到合适的格式，使用原始URL
            if not real_url:
                real_url = info.get('webpage_url', info.get('url', ''))
            
            logger.info(f"✅ 解析成功: {title}")
            return {
                "title": title,
                "real_download_url": real_url,
                "duration": info.get('duration'),
                "view_count": info.get('view_count'),
                "like_count": info.get('like_count'),
                "uploader": info.get('uploader'),
                "platform": "TikTok" if "tiktok.com" in url else "YouTube" if "youtube.com" in url else "Unknown"
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