# AstrBot 视频解析插件（Platform Parser）

这是一个针对 **AstrBot** 的视频解析插件，包含两个部分：

1. **AstrBot 插件** (`main.py`)：定义命令与逻辑，调用本地解析 API 服务。
2. **解析服务器** (`api.py`)：基于 FastAPI + yt_dlp，提供 `/parse` 和 `/download` 接口。

## 功能

- 支持 TikTok、抖音、YouTube 及其他平台视频链接解析。
- 提供可直接下载的视频真实地址或通过 API 下载。
- 插件自动读取并管理版本号，启动时会将 `metadata.yaml` 版本号 +0.01。
- 帮助命令包括 `/help_parse`、`/sphe` 等。

## 安装与部署

1. 克隆仓库到本地：
   ```bash
   git clone https://github.com/huanxherta/astrbot_platform_hx.git
   cd astrbot_platform_hx
   ```
2. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   pip install fastapi uvicorn yt-dlp
   ```
3. 在插件目录中运行解析服务（或使用进程管理器）：
   ```bash
   python api.py
   ```
   服务默认监听 `http://localhost:10010`。

4. 将本插件整个目录放到 AstrBot 的 `data/plugins/` 下，重启 AstrBot。

## AstrBot 插件命令

| 命令           | 说明                            |
| -------------- | ------------------------------- |
| `/parse <URL>` | 解析视频链接                    |
| `/api_status`  | 检查本地解析 API 服务状态       |
| `/ping_api`    | 测试与解析服务器的连接          |
| `/help_parse`  | 查看详细帮助                    |
| `/sphe`        | 快速显示帮助                    |
| `/test`        | 测试插件是否正常工作            |

解析结果示例：

```
✅ 解析成功！
```json
{
  "title": "Example Video",
  "real_download_url": "https://....mp4",
  "download_via_api": "http://localhost:10010/download?url=...",
  "platform": "YouTube",
  "duration": 123,
  "view_count": 45678,
  "uploader": "ChannelName"
}
```

## API 文档

- `POST /parse`：接收 JSON `{ "url": "..." }`，返回视频信息。
- `GET /download?url=...`：下载视频文件并返回。
- 健康检查：`GET /`, `/status`, `/ping`。

可以通过 `http://localhost:10010/docs` 查看 Swagger UI。

## 配置

- `www.youtube.com_cookies.txt`：可选的 YouTube cookie，用于解析需要登录的视频。
- `metadata.yaml`：插件元数据，`version` 字段由插件加载时自动更新。

## 许可证

见项目根目录中的 `LICENSE` 文件。