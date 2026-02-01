"""
飞书应用集成
包含Webhook接收器和消息处理器
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import hashlib
import hmac
import json
import base64
from datetime import datetime
from typing import Dict, Any
import uvicorn

from feishu_integration import NotificationService, FeishuEventHandler

app = FastAPI(title="飞书应用集成", version="1.0.0")

# 初始化通知服务
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d"
notification_service = NotificationService(WEBHOOK_URL)
event_handler = FeishuEventHandler(notification_service)

# 验证飞书请求的密钥（如果有的话）
APP_SECRET = ""  # 如果有应用密钥，请填入


def verify_signature(timestamp: str, sign: str) -> bool:
    """验证飞书请求签名"""
    if not APP_SECRET:
        return True  # 如果没有设置密钥则跳过验证
    
    secret = APP_SECRET.encode('utf-8')
    expected_sign = base64.b64encode(hmac.new(secret, 
                                             timestamp.encode('utf-8'), 
                                             digestmod=hashlib.sha256).digest()).decode()
    return hmac.compare_digest(expected_sign, sign)


@app.get("/")
async def root():
    return {
        "message": "飞书应用集成服务",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """
    飞书机器人Webhook接收器
    处理来自飞书的消息和事件
    """
    try:
        # 获取请求体
        body = await request.json()
        
        # 验证签名（如果设置了密钥）
        timestamp = request.headers.get('X-Lark-Request-Timestamp')
        sign = request.headers.get('X-Lark-Request-Nonce')
        
        if not verify_signature(timestamp or "", sign or ""):
            raise HTTPException(status_code=401, detail="签名验证失败")
        
        print(f"收到飞书请求: {body}")
        
        # 根据请求类型处理
        if "challenge" in body:
            # 首次验证请求，返回challenge
            return JSONResponse({"challenge": body["challenge"]})
        
        # 检查是否是消息事件
        if "event" in body:
            event = body["event"]
            event_type = event.get("type", "")
            
            if event_type == "message":
                # 处理消息事件
                message = event.get("message", {})
                chat_type = message.get("chat_type", "")
                text = message.get("text", "")
                
                # 解析消息内容
                response_text = handle_message(text)
                
                # 如果是群聊，发送回复消息
                if chat_type == "group" and response_text:
                    # 这里可以实现发送回复消息的逻辑
                    # 目前只记录日志
                    print(f"准备回复消息: {response_text}")
        
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        print(f"处理飞书Webhook请求时出错: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


def handle_message(text: str) -> str:
    """
    处理收到的消息
    """
    # 解析命令
    if text.startswith('/'):
        command_parts = text[1:].split(' ', 1)  # 去掉开头的 '/'
        command = command_parts[0].lower()
        params = command_parts[1].split() if len(command_parts) > 1 else []
        
        return event_handler.handle_command(command, params)
    elif text.startswith('通知'):
        # 处理通知命令
        message = text[2:].strip()  # 去掉开头的"通知"
        if message:
            notification_service.send_system_notification("手动通知", message)
            return f"已发送通知: {message}"
        else:
            return "请提供要通知的内容"
    else:
        # 普通消息，返回帮助信息
        return event_handler.get_help_text()


@app.post("/feishu/notify/system")
async def notify_system(request: Request):
    """发送系统通知"""
    try:
        data = await request.json()
        title = data.get("title", "系统通知")
        message = data.get("message", "系统消息")
        priority = data.get("priority", "normal")
        
        result = notification_service.send_system_notification(
            title, message, priority
        )
        
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/feishu/notify/flight")
async def notify_flight(request: Request):
    """发送飞行通知"""
    try:
        data = await request.json()
        flight_id = data.get("flight_id", "UNKNOWN")
        event = data.get("event", "飞行事件")
        details = data.get("details", {})
        
        result = notification_service.send_flight_notification(
            flight_id, event, details
        )
        
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/feishu/notify/wish")
async def notify_wish(request: Request):
    """发送许愿通知"""
    try:
        data = await request.json()
        wish_content = data.get("content", "")
        likes = data.get("likes", 0)
        
        result = notification_service.send_wish_notification(
            wish_content, likes
        )
        
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/feishu/notify/landing")
async def notify_landing(request: Request):
    """发送降落通知"""
    try:
        data = await request.json()
        status = data.get("status", "未知状态")
        details = data.get("details", {})
        
        result = notification_service.send_landing_notification(
            status, details
        )
        
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.get("/feishu/status")
async def feishu_status():
    """获取飞书集成状态"""
    return {
        "status": "connected",
        "webhook_url_set": bool(WEBHOOK_URL),
        "timestamp": datetime.now().isoformat(),
        "features": [
            "system_notifications",
            "flight_notifications", 
            "wish_notifications",
            "landing_notifications",
            "command_handling"
        ]
    }


# 测试函数
def test_feishu_integration():
    """测试飞书集成功能"""
    print("🧪 开始测试飞书集成...")
    
    # 测试发送不同类型的通知
    print("\n1. 测试系统通知...")
    result = notification_service.send_system_notification(
        "测试标题", 
        "这是一条测试消息", 
        "high"
    )
    print(f"   结果: {result}")
    
    print("\n2. 测试飞行通知...")
    result = notification_service.send_flight_notification(
        "TEST001", 
        "测试事件", 
        {"高度": "100m", "电量": "90%"}
    )
    print(f"   结果: {result}")
    
    print("\n3. 测试许愿通知...")
    result = notification_service.send_wish_notification(
        "测试愿望", 
        10
    )
    print(f"   结果: {result}")
    
    print("\n4. 测试命令处理...")
    result = event_handler.handle_command("status")
    print(f"   状态命令结果: {result}")
    
    print("\n✅ 飞书集成测试完成")


if __name__ == "__main__":
    # 首先运行测试
    test_feishu_integration()
    
    print("\n🚀 启动飞书应用集成服务...")
    uvicorn.run(app, host="0.0.0.0", port=8004)