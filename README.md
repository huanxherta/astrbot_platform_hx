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
| `/parse <URL>` | 解析视频链接（会返回解析信息并尝试下载发送）|
| `/api_status`  | 检查本地解析 API 服务状态       |
| `/ping_api`    | 测试与解析服务器的连接          |
| `/help_parse`  | 查看详细帮助                    |
| `/sphe`        | 快速显示帮助                    |
| `/test`        | 测试插件是否正常工作            |

解析结果示例：

以下为真实运行日志和输出：
```
[2026-03-04 09:17:57.552] [Core] [INFO] [core.event_bus:59]: [default] [napcat(aiocqhttp)] hc/3500372287: 。parse https://x.com/i/status/2028656600328831320
[2026-03-04 09:17:57.558] [Plug] [INFO] [astrbot_platform_hx.main:66]: 开始解析视频: https://x.com/i/status/2028656600328831320
[2026-03-04 09:18:00.424] [Plug] [INFO] [astrbot_platform_hx.main:73]: API响应状态: 200
[2026-03-04 09:18:00.425] [Plug] [INFO] [astrbot_platform_hx.main:80]: 解析结果: {...}
[2026-03-04 09:18:05.462] [Core] [INFO] [respond.stage:184]: Prepare to send - hc/3500372287: ✅ 解析成功！
[CQ:file,file=/root/astrbot/2028656380400541696.mp4]
```

> ⚠️ 对于 YouTube 链接，插件会将解析超时设置为 **40 秒**，以应对较慢的响应。

*原有的 `/download` 命令已移除，解析结果中包含 `download_via_api` 字段，可直接访问下载接口。解析命令会自动尝试下载视频并生成 CQ 码（仅在支持 CQ 的适配器上有效）。*


```
✅ 解析成功！
```json
{
  "title": "エンドフィールド工房 - アホかwww  ©️水霓代子 #エンドフィールド #ArknightsEndfield",
  "real_download_url": "https://video.twimg.com/amplify_video/2028656380400541696/vid/avc1/720x960/ZvuPZzSvdiyqiEzy.mp4?tag=14",
  "download_via_api": "http://localhost:10010/download?url=https%3A%2F%2Fx.com%2Fi%2Fstatus%2F2028656600328831320",
  "platform": "Unknown",
  "duration": 12.585,
  "view_count": null,
  "uploader": "エンドフィールド工房"
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