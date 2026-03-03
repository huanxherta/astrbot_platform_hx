# 视频解析API服务器

## 🚀 快速启动

### 方法1：使用启动脚本
```bash
python start_api.py
```

### 方法2：直接运行
```bash
python api.py
```

### 方法3：安装依赖后运行
```bash
pip install -r api_requirements.txt
python api.py
```

## 📡 API地址

- **服务地址**: http://localhost:10010
- **API文档**: http://localhost:10010/docs
- **健康检查**: http://localhost:10010/status

## 🔌 API使用

### 解析视频
```bash
curl -X POST "http://localhost:10010/parse" \
     -H "Content-Type: application/json" \
     -d '{"url": "你的视频链接"}'
```

### 支持的平台
- ✅ TikTok (抖音)
- ✅ YouTube
- ✅ 其他 yt-dlp 支持的平台

## 🔧 特性

- 🎯 智能格式选择
- 📱 平台检测
- 🍪 YouTube Cookie 支持
- 📊 详细视频信息
- 🛡️ 错误处理
- 📝 详细日志

## 📝 响应格式

```json
{
  "title": "视频标题",
  "real_download_url": "下载链接",
  "duration": 视频长度,
  "view_count": 观看次数,
  "like_count": 点赞数,
  "uploader": "上传者",
  "platform": "TikTok/YouTube"
}
```

## 🔍 故障排除

1. **端口被占用**
   ```bash
   sudo lsof -i :10010
   ```

2. **依赖问题**
   ```bash
   pip install -r api_requirements.txt
   ```

3. **防火墙问题**
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="API Server" dir=in action=allow protocol=TCP localport=10010
   
   # Linux
   sudo ufw allow 10010
   ```