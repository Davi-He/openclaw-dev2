# 飞书机器人聊天功能

## 概述
飞书机器人现在专注于对话功能，可以响应@消息和命令，提供系统信息查询服务。

Webhook URL: `https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d`

## 支持的命令

### 对话命令
- `@机器人 /status` - 查看系统状态
- `@机器人 /wishes` - 查看许愿小程序信息
- `@机器人 /flight` - 查看飞行系统信息
- `@机器人 /landing` - 查看降落系统信息
- `@机器人 /time` - 查看当前时间
- `@机器人 /services` - 查看所有服务信息
- `@机器人 /help` - 显示帮助信息

### 自然语言支持
- `@机器人 状态` - 等同于 `/status`
- `@机器人 飞行` - 等同于 `/flight`
- `@机器人 降落` - 等同于 `/landing`
- `@机器人 愿望` - 等同于 `/wishes`

## 配置要求

### 飞书开发者后台配置
1. 在事件订阅中添加 `im.message.receive_v1` 事件
2. 设置回调URL为：`http://<YOUR_SERVER_IP>:8004/feishu/webhook`
3. 确保机器人具有消息读取权限

### 服务状态
- **服务地址**: http://localhost:8004
- **健康检查**: http://localhost:8004/feishu/status
- **Webhook端点**: http://localhost:8004/feishu/webhook

## 特性
- 无主动推送通知
- 仅响应@消息和命令
- 提供丰富的系统信息查询
- 支持自然语言理解
- 快速响应时间