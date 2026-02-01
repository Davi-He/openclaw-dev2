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

from feishu_chat import ChatService, FeishuChatHandler

app = FastAPI(title="飞书应用集成", version="1.0.0")

# 初始化聊天服务
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d"
chat_service = ChatService(WEBHOOK_URL)
chat_handler = FeishuChatHandler(chat_service)

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
        sign = request.headers.get('X-Lark-Request-Signature')
        
        if not verify_signature(timestamp or "", sign or ""):
            raise HTTPException(status_code=401, detail="签名验证失败")
        
        print(f"收到飞书请求: {body}")
        
        # 根据请求类型处理
        if "challenge" in body:
            # 首次验证请求，返回challenge
            return JSONResponse({"challenge": body["challenge"]})
        
        # 检查是否是消息事件
        if "header" in body and body["header"]["event_type"] == "im.message.receive_v1":
            # 处理新消息事件
            event = body.get("event", {})
            message = event.get("message", {})
            
            if message.get("msg_type") == "text":
                # 处理文本消息
                chat_id = message.get("chat_id")
                message_id = message.get("message_id")
                sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id", "")
                
                # 获取消息内容
                content = message.get("content", "")
                try:
                    # 解析JSON格式的内容
                    content_data = json.loads(content)
                    text = content_data.get("text", "").strip()
                except:
                    text = content.strip()
                
                # 检查是否@了机器人
                mentions = message.get("mentions", [])
                is_mentioned = any(mention.get("name") == "openclaw-bot" for mention in mentions)  # 替换为实际的机器人名称
                
                print(f"收到消息: {text}, 是否@机器人: {is_mentioned}, 发送者: {sender_id}")
                
                # 处理消息
                response_text = handle_message(text, is_mentioned)
                
                # 如果有回复内容，发送回复
                if response_text:
                    # 发送回复消息
                    await send_reply_message(chat_id, message_id, response_text)
        
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        print(f"处理飞书Webhook请求时出错: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


async def send_reply_message(chat_id: str, message_id: str, text: str):
    """
    发送回复消息到飞书
    """
    # 注意：实际发送消息需要使用飞书开放平台的接口
    # 这里仅做演示，实际使用时需要获取app_access_token等
    print(f"准备发送回复消息到聊天 {chat_id}, 消息ID: {message_id}, 内容: {text}")
    
    # 在实际实现中，需要调用飞书API发送消息
    # 这里只是记录日志
    pass


def handle_message(text: str, is_mentioned: bool = False) -> str:
    """
    处理收到的消息
    """
    # 如果是@机器人或消息以/开头，则处理命令
    if is_mentioned or text.startswith('/'):
        # 清理消息内容，去掉@部分
        clean_text = text
        if '@' in text:
            # 简单去除@部分，实际实现中可能需要更复杂的解析
            parts = text.split(' ')
            clean_text = ' '.join([part for part in parts if not part.startswith('@')])
        
        # 解析命令
        if clean_text.strip().startswith('/'):
            command_parts = clean_text[1:].split(' ', 1)  # 去掉开头的 '/'
            command = command_parts[0].lower()
            params = command_parts[1].split() if len(command_parts) > 1 else []
            
            return chat_handler.process_command(command, params)
        else:
            # 处理自然语言命令
            clean_text = clean_text.strip().lower()
            if '状态' in clean_text or 'status' in clean_text:
                return chat_handler.process_command("status")
            elif '愿望' in clean_text or 'wish' in clean_text:
                return chat_handler.process_command("wishes")
            elif '飞行' in clean_text or 'flight' in clean_text:
                return chat_handler.process_command("flight")
            elif '降落' in clean_text or 'landing' in clean_text:
                return chat_handler.process_command("landing")
            elif '帮助' in clean_text or 'help' in clean_text:
                return chat_handler.get_help_text()
            else:
                # 尝试解析为命令
                return chat_handler.process_command(clean_text.split()[0] if clean_text.split() else "help")
    elif text.strip().lower() in ['你好', 'hello', 'hi', '您好']:
        return chat_handler.get_greeting()
    else:
        # 普通消息，返回帮助信息
        return chat_handler.get_help_text()


# 移除通知API端点，专注于聊天功能


@app.get("/feishu/status")
async def feishu_status():
    """获取飞书集成状态"""
    return {
        "status": "connected",
        "webhook_url_set": bool(WEBHOOK_URL),
        "timestamp": datetime.now().isoformat(),
        "features": [
            "chat_interface",
            "command_handling",
            "system_info",
            "wishes_info",
            "flight_info",
            "landing_info"
        ]
    }


# 测试函数
def test_feishu_integration():
    """测试飞书集成功能"""
    print("🧪 开始测试飞书集成...")
    
    # 测试命令处理
    print("\n1. 测试状态命令...")
    result = chat_handler.process_command("status")
    print(f"   状态命令结果: {result}")
    
    print("\n2. 测试许愿命令...")
    result = chat_handler.process_command("wishes")
    print(f"   许愿命令结果: {result}")
    
    print("\n3. 测试飞行命令...")
    result = chat_handler.process_command("flight")
    print(f"   飞行命令结果: {result}")
    
    print("\n4. 测试降落命令...")
    result = chat_handler.process_command("landing")
    print(f"   降落命令结果: {result}")
    
    print("\n5. 测试帮助命令...")
    result = chat_handler.get_help_text()
    print(f"   帮助命令结果: {result}")
    
    print("\n✅ 飞书集成测试完成")


if __name__ == "__main__":
    # 首先运行测试
    test_feishu_integration()
    
    print("\n🚀 启动飞书聊天服务...")
    uvicorn.run(app, host="0.0.0.0", port=8004)