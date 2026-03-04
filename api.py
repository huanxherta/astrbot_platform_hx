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
import asyncio
import datetime
from datetime import timedelta
from typing import Dict, Any as AnyT

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


@app.delete("/download")
async def delete_video(url: str):
    """删除已缓存的下载文件（仅在 downloads/ 目录内）。

    Args:
        url: 原始视频 URL，用于计算下载文件名并删除对应文件。
    """
    logger.info(f"🗑️ 收到删除请求: {url}")
    download_dir = os.path.join(os.path.dirname(__file__), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    try:
        ydl_opts = _build_ydl_opts(url)
        ydl_opts.update({
            'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
            'noplaylist': True,
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 只获取信息，计算目标文件名
            info = ydl.extract_info(url, download=False)
            if not info:
                raise HTTPException(status_code=400, detail="无法获取视频信息，无法删除")

            file_path = ydl.prepare_filename(info)

            # 仅允许删除 downloads 下的文件，防止任意文件删除
            real_download_dir = os.path.realpath(download_dir)
            real_file_path = os.path.realpath(file_path)
            if not real_file_path.startswith(real_download_dir + os.sep):
                logger.error(f"尝试删除不在 downloads 目录的文件: {real_file_path}")
                raise HTTPException(status_code=400, detail="拒绝删除非缓存目录文件")

            if os.path.exists(real_file_path):
                try:
                    os.remove(real_file_path)
                    logger.info(f"✅ 已删除缓存文件: {real_file_path}")
                    return {"deleted": True, "path": real_file_path}
                except Exception as e:
                    logger.error(f"删除文件失败: {e}")
                    raise HTTPException(status_code=500, detail=f"删除失败: {e}")
            else:
                logger.info(f"未找到要删除的文件: {real_file_path}")
                raise HTTPException(status_code=404, detail="未找到缓存文件")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        logger.error(f"❌ 删除异常: {err}")
        raise _normalize_error_detail(e, url)


# ----------------
# 下载目录周期清理任务
# ----------------

# 全局下载目录常量（模块级）
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 可通过环境变量覆盖
DOWNLOAD_RETENTION_DAYS = int(os.getenv("DOWNLOAD_RETENTION_DAYS", "7"))
# 清理间隔（秒），默认每天一次
DOWNLOAD_CLEANUP_INTERVAL = int(os.getenv("DOWNLOAD_CLEANUP_INTERVAL", str(24 * 3600)))

def _cleanup_once(retention_days: int = DOWNLOAD_RETENTION_DAYS) -> Dict[str, AnyT]:
    now = datetime.datetime.now()
    cutoff = now - timedelta(days=retention_days)
    removed_files = []

    try:
        for root, _, files in os.walk(DOWNLOAD_DIR):
            for fn in files:
                fp = os.path.join(root, fn)
                try:
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
                except Exception:
                    continue
                if mtime < cutoff:
                    try:
                        os.remove(fp)
                        removed_files.append(fp)
                        logger.info(f"🧹 已删除过期缓存文件: {fp}")
                    except Exception as e:
                        logger.error(f"删除文件失败 {fp}: {e}")
        return {"deleted_count": len(removed_files), "deleted": removed_files}
    except Exception as e:
        logger.error(f"清理异常: {e}")
        return {"deleted_count": 0, "deleted": [], "error": str(e)}

async def _periodic_cleanup_task(interval: int = DOWNLOAD_CLEANUP_INTERVAL, retention_days: int = DOWNLOAD_RETENTION_DAYS):
    logger.info(f"启动下载目录周期清理任务: 每 {interval}s 清理一次，保留 {retention_days} 天内的文件")
    while True:
        try:
            res = _cleanup_once(retention_days)
            if res.get("deleted_count", 0) > 0:
                logger.info(f"清理完成，移除 {res['deleted_count']} 个文件")
        except Exception as e:
            logger.error(f"周期清理出错: {e}")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_cleanup_task():
    # 在后台启动周期清理任务
    asyncio.create_task(_periodic_cleanup_task())


@app.post("/cleanup")
async def trigger_cleanup(dry_run: bool = False):
    """手动触发一次清理。默认会删除过期文件；dry_run=True 时仅返回将被删除的列表。"""
    # 返回将要删除或已删除的文件信息
    if dry_run:
        # 模拟：列出但不删除
        now = datetime.datetime.now()
        cutoff = now - timedelta(days=DOWNLOAD_RETENTION_DAYS)
        will_delete = []
        for root, _, files in os.walk(DOWNLOAD_DIR):
            for fn in files:
                fp = os.path.join(root, fn)
                try:
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
                except Exception:
                    continue
                if mtime < cutoff:
                    will_delete.append(fp)
        return {"will_delete_count": len(will_delete), "will_delete": will_delete}

    return _cleanup_once(DOWNLOAD_RETENTION_DAYS)

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
