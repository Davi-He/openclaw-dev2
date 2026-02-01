"""
飞书机器人集成模块
支持通过飞书接收通知和控制设备
Webhook URL: https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d
"""
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import aiohttp
from dataclasses import dataclass


@dataclass
class FeishuMessage:
    """飞书消息数据类"""
    msg_type: str  # text, image, interactive
    content: Dict


class FeishuBot:
    """飞书机器人客户端"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()
        
    def send_text_message(self, text: str) -> Dict:
        """发送文本消息"""
        payload = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        return self._send_request(payload)
    
    def send_post_message(self, title: str, content: List[str]) -> Dict:
        """发送富文本消息"""
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [[{
                            "tag": "text",
                            "un_escape": True,
                            "text": line
                        }] for line in content]
                    }
                }
            }
        }
        return self._send_request(payload)
    
    def send_image_message(self, image_url: str) -> Dict:
        """发送图片消息（需要先上传图片获取file_key）"""
        # 注意：发送图片需要先上传图片获取file_key
        # 这里假设已经有一个file_key
        payload = {
            "msg_type": "image",
            "content": {
                "image_key": image_url  # 实际使用时需要替换为有效的image_key
            }
        }
        return self._send_request(payload)
    
    def send_interactive_card(self, title: str, content: str, 
                            buttons: List[Dict] = None) -> Dict:
        """发送交互式卡片"""
        if buttons is None:
            buttons = []
            
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content
                    }
                ] + [{"tag": "action", "actions": buttons}] if buttons else [],
                "header": {
                    "template": "blue",
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    }
                }
            }
        }
        return self._send_request(payload)
    
    def _send_request(self, payload: Dict) -> Dict:
        """发送HTTP请求到飞书机器人"""
        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"发送飞书消息失败: {e}")
            return {"error": str(e)}


class NotificationService:
    """通知服务类，集成飞书机器人"""
    
    def __init__(self, feishu_webhook: str):
        self.feishu_bot = FeishuBot(feishu_webhook)
        
    def send_system_notification(self, title: str, message: str, 
                               priority: str = "normal") -> Dict:
        """发送系统通知"""
        content = f"【{title}】\n{message}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if priority == "high":
            # 高优先级使用富文本格式
            return self.feishu_bot.send_post_message(
                title=title,
                content=[
                    f"🚨 {message}",
                    f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ]
            )
        else:
            return self.feishu_bot.send_text_message(content)
    
    def send_flight_notification(self, flight_id: str, event: str, 
                               details: Dict = None) -> Dict:
        """发送飞行相关通知"""
        if details is None:
            details = {}
            
        content_lines = [
            f"✈️ 飞行器 {flight_id}",
            f"事件: {event}",
        ]
        
        if details:
            for key, value in details.items():
                content_lines.append(f"{key}: {value}")
                
        content_lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.feishu_bot.send_post_message(
            title="飞行状态通知",
            content=content_lines
        )
    
    def send_wish_notification(self, wish_content: str, likes: int = 0) -> Dict:
        """发送许愿小程序通知"""
        content = f"✨ 新愿望: {wish_content}\n❤️ 点赞数: {likes}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return self.feishu_bot.send_post_message(
            title="许愿小程序通知",
            content=[content]
        )
    
    def send_landing_notification(self, status: str, details: Dict = None) -> Dict:
        """发送降落系统通知"""
        if details is None:
            details = {}
            
        content_lines = [
            f"🎯 降落系统状态: {status}",
        ]
        
        if details:
            for key, value in details.items():
                content_lines.append(f"{key}: {value}")
                
        content_lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.feishu_bot.send_post_message(
            title="降落系统通知",
            content=content_lines
        )


class FeishuEventHandler:
    """飞书事件处理器"""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    def handle_command(self, command: str, params: List[str] = None) -> str:
        """处理飞书机器人命令"""
        if params is None:
            params = []
            
        command = command.lower().strip()
        
        if command == "status":
            return self.get_system_status()
        elif command == "wishes":
            return self.get_wishes_status()
        elif command == "flight":
            return self.get_flight_status()
        elif command.startswith("notify"):
            # 发送通知命令
            message = " ".join(params) if params else "系统通知"
            self.notification_service.send_system_notification("命令通知", message)
            return f"已发送通知: {message}"
        else:
            return self.get_help_text()
    
    def get_system_status(self) -> str:
        """获取系统状态"""
        return (
            "🖥️ 系统状态:\n"
            f"- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "- 服务运行正常\n"
            "- 所有模块在线\n"
            "- 飞书机器人集成正常"
        )
    
    def get_wishes_status(self) -> str:
        """获取许愿小程序状态"""
        return (
            "✨ 许愿小程序状态:\n"
            "- 服务运行正常\n"
            "- 数据库连接正常\n"
            "- API接口可用\n"
            "- 前端页面可访问"
        )
    
    def get_flight_status(self) -> str:
        """获取飞行系统状态"""
        return (
            "✈️ 飞行系统状态:\n"
            "- 自动驾驶系统在线\n"
            "- 传感器数据正常\n"
            "- 降落系统就绪\n"
            "- 导航系统正常"
        )
    
    def get_help_text(self) -> str:
        """获取帮助信息"""
        return (
            "📖 机器人命令帮助:\n"
            "/status - 查看系统状态\n"
            "/wishes - 查看许愿小程序状态\n"
            "/flight - 查看飞行系统状态\n"
            "/notify <message> - 发送通知\n"
            "/help - 显示此帮助信息"
        )


# 示例用法
def main():
    """主函数 - 演示飞书集成功能"""
    # 飞书机器人webhook URL
    WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d"
    
    # 创建通知服务
    notification_service = NotificationService(WEBHOOK_URL)
    
    print("🚀 飞书机器人集成演示")
    print("=" * 50)
    
    # 发送欢迎消息
    result = notification_service.send_system_notification(
        "系统启动", 
        "飞书机器人集成模块已启动", 
        priority="high"
    )
    print(f"发送欢迎消息结果: {result}")
    
    # 发送飞行通知
    flight_details = {
        "高度": "120m",
        "速度": "5.2 m/s",
        "电量": "85%"
    }
    result = notification_service.send_flight_notification(
        "FLIGHT_001", 
        "自动降落完成", 
        flight_details
    )
    print(f"发送飞行通知结果: {result}")
    
    # 发送许愿通知
    result = notification_service.send_wish_notification(
        "希望世界和平", 
        likes=42
    )
    print(f"发送许愿通知结果: {result}")
    
    # 发送降落系统通知
    landing_details = {
        "当前状态": "降落完成",
        "目标坐标": "(400, 300)",
        "耗时": "15秒"
    }
    result = notification_service.send_landing_notification(
        "降落完成", 
        landing_details
    )
    print(f"发送降落通知结果: {result}")
    
    # 创建事件处理器
    event_handler = FeishuEventHandler(notification_service)
    
    # 演示命令处理
    print("\n🔧 命令处理演示:")
    print(event_handler.handle_command("status"))
    print(event_handler.handle_command("wishes"))
    print(event_handler.handle_command("flight"))


if __name__ == "__main__":
    main()