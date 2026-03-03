# AstrBot Plugin Template

这是一个AstrBot插件模板项目。

## 使用方法

1. 修改 `metadata.yaml` 中的插件信息：
   - name: 插件名称
   - author: 作者
   - desc: 插件描述
   - version: 版本号
   - repo: 你的插件仓库地址

2. 在 `main.py` 中编写你的插件逻辑

3. 将插件放入AstrBot的 `data/plugins/` 目录下

## 插件结构

- `metadata.yaml`: 插件元数据配置
- `main.py`: 插件主要代码
- `icon.png`: 插件图标（可选）

## 开发说明

- 使用 `@register` 装饰器注册插件
- 使用 `@filter.command` 装饰器注册命令
- 通过 `event.send()` 发送消息
- 通过 `event.message` 获取消息内容

## 示例命令

- `/hello` - 发送问候消息
- `/ping` - 测试响应