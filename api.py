from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget
import uvicorn
import logging
import os
import re
from typing import Any, cast
from urllib.parse import quote

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoItem(BaseModel):
    url: str


def _build_ydl_opts(url: str) -> dict[str, Any]:
    ydl_opts: dict[str, Any] = {
        'format': 'best[ext=mp4]/best',
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'extract_flat': False,
        'ignoreerrors': False,
    }

    if 'tiktok.com' in url or 'douyin.com' in url:
        logger.info("📱 检测到TikTok/抖音链接")
        ydl_opts['impersonate'] = ImpersonateTarget('chrome')
    elif 'youtube.com' in url or 'youtu.be' in url:
        logger.info("📺 检测到YouTube链接")
        cookie_path = os.path.join(os.path.dirname(__file__), "www.youtube.com_cookies.txt")
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
            logger.info(f"🍪 加载Cookie: {cookie_path}")
        else:
            logger.warning("⚠️ 未找到Cookie文件，匿名解析")
    else:
        logger.info("🌐 其他平台链接")

    return ydl_opts


def _normalize_error_detail(err: Exception, url: str) -> HTTPException:
    detail = str(err) if str(err) else repr(err)
    detail = re.sub(r'\x1b\[[0-9;]*m', '', detail).strip()

    if ('tiktok.com' in url or 'douyin.com' in url) and '/hk/notfound' in detail:
        return HTTPException(
            status_code=400,
            detail="TikTok分享链接已失效、被下架或地区不可用，请改用可直接打开的原始视频链接（https://www.tiktok.com/@xxx/video/xxx）"
        )

    return HTTPException(status_code=500, detail=detail)

@app.post("/parse")
async def parse_video(item: VideoItem):
    url = item.url
    logger.info(f"🚀 收到解析任务: {url}")

    try:
        ydl_opts = _build_ydl_opts(url)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            raw_info = ydl.extract_info(url, download=False)

            if not raw_info or not isinstance(raw_info, dict):
                raise HTTPException(status_code=400, detail="无法获取视频信息（info为空）")

            info = cast(dict[str, Any], raw_info)
            title = info.get('title', 'Unknown Video')
            real_url = None

            # 从formats中查找最佳链接
            formats = info.get('formats', [])
            if isinstance(formats, list):
                normalized_formats = [f for f in formats if isinstance(f, dict)]
                for fmt in sorted(normalized_formats, key=lambda x: x.get('height', 0) or 0, reverse=True):
                    fmt_url = fmt.get('url', '')
                    if fmt_url and fmt.get('vcodec') != 'none' and 'm3u8' not in str(fmt_url):
                        real_url = str(fmt_url)
                        break

            if not real_url:
                real_url = str(info.get('webpage_url') or info.get('url') or '')

            platform = "TikTok" if "tiktok.com" in url else "YouTube" if "youtube.com" in url else "Unknown"
            download_api_url = f"http://localhost:10010/download?url={quote(url, safe='')}"
            logger.info(f"✅ 解析成功: {title}")

            return {
                "title": title,
                "real_download_url": real_url,
                "download_via_api": download_api_url,
                "platform": platform,
                "duration": info.get('duration'),
                "view_count": info.get('view_count'),
                "uploader": info.get('uploader'),
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        logger.error(f"❌ 解析异常: {err}")
        raise _normalize_error_detail(e, url)

@app.get("/download")
async def download_video(url: str):
    logger.info(f"⬇️ 收到下载任务: {url}")
    download_dir = os.path.join(os.path.dirname(__file__), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    try:
        ydl_opts = _build_ydl_opts(url)
        ydl_opts.update({
            'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
            'noplaylist': True,
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise HTTPException(status_code=400, detail="下载失败：无法获取视频信息")

            file_path = ydl.prepare_filename(info)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=500, detail="下载失败：未找到下载文件")

            logger.info(f"✅ 下载完成: {file_path}")
            return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        logger.error(f"❌ 下载异常: {err}")
        raise _normalize_error_detail(e, url)

@app.get("/")
async def root():
    return {"message": "视频解析API服务运行中", "endpoints": {"parse": "POST /parse", "download": "GET /download?url=..."}}

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
