# 飞书机器人集成文档

## 概述
本项目集成了飞书机器人功能，支持通过飞书接收系统通知和控制设备。Webhook URL: `https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d`

## 功能特性

### 1. 系统通知
- 发送系统状态通知
- 支持高低优先级通知
- 实时系统监控提醒

### 2. 飞行通知
- 飞行器状态更新
- 自动驾驶事件通知
- 降落完成提醒

### 3. 许愿小程序通知
- 新愿望发布提醒
- 点赞数更新通知
- 活跃度统计

### 4. 降落系统通知
- 降落状态更新
- 安全等级提醒
- 任务完成确认

## API 接口

### 系统通知
```
POST /feishu/notify/system
Content-Type: application/json

{
  "title": "通知标题",
  "message": "通知内容", 
  "priority": "normal/high"
}
```

### 飞行通知
```
POST /feishu/notify/flight
Content-Type: application/json

{
  "flight_id": "飞行器ID",
  "event": "事件描述",
  "details": {
    "高度": "120m",
    "电量": "85%"
  }
}
```

### 许愿通知
```
POST /feishu/notify/wish
Content-Type: application/json

{
  "content": "愿望内容",
  "likes": 42
}
```

### 降落通知
```
POST /feishu/notify/landing
Content-Type: application/json

{
  "status": "降落状态",
  "details": {
    "目标坐标": "(400, 300)",
    "耗时": "15秒"
  }
}
```

### 状态查询
```
GET /feishu/status
```

## 命令支持

机器人支持以下命令：

- `/status` - 查看系统状态
- `/wishes` - 查看许愿小程序状态
- `/flight` - 查看飞行系统状态
- `/notify <message>` - 发送自定义通知
- `/help` - 显示帮助信息

## 部署信息

- **服务地址**: http://localhost:8004
- **Webhook接收器**: http://localhost:8004/feishu/webhook
- **状态接口**: http://localhost:8004/feishu/status

## 集成方式

1. 在飞书开发者平台创建机器人
2. 配置Webhook URL为 `http://<your-domain>:8004/feishu/webhook`
3. 根据需要配置事件订阅
4. 机器人将自动响应命令和发送通知

## 安全考虑

- Webhook请求验证（如有设置密钥）
- 输入参数校验
- 错误处理和日志记录