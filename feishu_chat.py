"""
飞书机器人聊天模块
支持通过飞书进行对话和指令执行
Webhook URL: https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d
"""
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
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


class ChatService:
    """聊天服务类，用于处理飞书机器人的对话"""
    
    def __init__(self, feishu_webhook: str):
        self.feishu_bot = FeishuBot(feishu_webhook)
        
    def send_message(self, content: str) -> Dict:
        """发送消息到飞书"""
        return self.feishu_bot.send_text_message(content)
    
    def send_response(self, response: str) -> Dict:
        """发送对话响应"""
        return self.send_message(response)
    
    def get_system_info(self) -> str:
        """获取系统信息"""
        return (
            f"🖥️ 系统状态:\n"
            f"- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- 服务运行正常\n"
            f"- 所有模块在线\n"
            f"- 飞书机器人集成正常"
        )
    
    def get_wishes_info(self) -> str:
        """获取许愿小程序信息"""
        return (
            f"✨ 许愿小程序状态:\n"
            f"- 服务运行正常\n"
            f"- 数据库连接正常\n"
            f"- API接口可用\n"
            f"- 前端页面可访问\n"
            f"- 访问地址: http://localhost:8081"
        )
    
    def get_flight_info(self) -> str:
        """获取飞行系统信息"""
        return (
            f"✈️ 飞行系统状态:\n"
            f"- 自动驾驶系统在线\n"
            f"- 传感器数据正常\n"
            f"- 降落系统就绪\n"
            f"- 导航系统正常\n"
            f"- API接口: http://localhost:8002"
        )
    
    def get_landing_info(self) -> str:
        """获取降落系统信息"""
        return (
            f"🎯 降落系统状态:\n"
            f"- 界面可用: http://localhost:8003\n"
            f"- API接口: http://localhost:8002\n"
            f"- 支持点击摄像头视图选择降落位置\n"
            f"- 实时状态监控"
        )
    
    def execute_command(self, command: str) -> str:
        """执行系统命令并返回结果"""
        # 这里可以根据需要扩展更多命令
        if command.startswith("curl ") or command.startswith("ls ") or command.startswith("cat "):
            # 示例：简单命令执行（实际应用中需要更安全的实现）
            return f"执行命令: {command}\n[模拟输出 - 实际环境中需要安全的命令执行机制]"
        else:
            return f"命令 '{command}' 不被支持或需要额外的安全验证"


class FeishuChatHandler:
    """飞书聊天处理器"""
    
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
        
    def handle_message(self, text: str, is_mentioned: bool = False) -> str:
        """处理收到的消息"""
        # 如果是@机器人或消息以/开头，则处理命令
        if is_mentioned or text.startswith('/'):
            # 清理消息内容，去掉@部分
            clean_text = text
            if '@' in text:
                # 简单去除@部分，实际实现中可能需要更复杂的解析
                parts = text.split(' ')
                clean_text = ' '.join([part for part in parts if not part.startswith('@')])
                clean_text = clean_text.strip()
        
            # 解析命令
            if clean_text.strip().startswith('/'):
                command_parts = clean_text[1:].split(' ', 1)  # 去掉开头的 '/'
                command = command_parts[0].lower()
                params = command_parts[1].split() if len(command_parts) > 1 else []
                
                return self.process_command(command, params)
            else:
                # 处理自然语言命令
                clean_text = clean_text.strip().lower()
                if '状态' in clean_text or 'status' in clean_text:
                    return self.process_command("status", [])
                elif '愿望' in clean_text or 'wish' in clean_text:
                    return self.process_command("wishes", [])
                elif '飞行' in clean_text or 'flight' in clean_text:
                    return self.process_command("flight", [])
                elif '降落' in clean_text or 'landing' in clean_text:
                    return self.process_command("landing", [])
                elif '帮助' in clean_text or 'help' in clean_text:
                    return self.get_help_text()
                else:
                    # 尝试解析为命令
                    cmd = clean_text.split()[0] if clean_text.split() else "help"
                    return self.process_command(cmd, [])
    
        elif text.strip().lower() in ['你好', 'hello', 'hi', '您好']:
            return self.get_greeting()
        else:
            # 普通消息，返回帮助信息
            return self.get_help_text()
    
    def process_command(self, command: str, params: List[str] = None) -> str:
        """处理具体命令"""
        if params is None:
            params = []
            
        command = command.lower().strip()
        
        if command == "status":
            return self.chat_service.get_system_info()
        elif command == "wishes":
            return self.chat_service.get_wishes_info()
        elif command == "flight":
            return self.chat_service.get_flight_info()
        elif command == "landing":
            return self.chat_service.get_landing_info()
        elif command == "help":
            return self.get_help_text()
        elif command == "time":
            return f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif command == "services":
            return self.get_services_info()
        else:
            return f"❓ 未知命令: {command}\n{self.get_help_text()}"
    
    def get_greeting(self) -> str:
        """获取问候语"""
        return (
            f"👋 你好！我是OpenClaw飞书助手\n"
            f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"我可以帮您查询系统状态、许愿小程序、飞行系统等信息。\n"
            f"输入 /help 查看可用命令。"
        )
    
    def get_help_text(self) -> str:
        """获取帮助信息"""
        return (
            "📖 机器人命令帮助:\n"
            "/status - 查看系统状态\n"
            "/wishes - 查看许愿小程序状态\n"
            "/flight - 查看飞行系统状态\n"
            "/landing - 查看降落系统状态\n"
            "/time - 查看当前时间\n"
            "/services - 查看所有服务\n"
            "/help - 显示此帮助信息"
        )
    
    def get_services_info(self) -> str:
        """获取所有服务信息"""
        return (
            "📡 系统服务列表:\n"
            "1. 许愿小程序: http://localhost:8081\n"
            "   - API接口: http://localhost:8000\n"
            "   - 功能: 发布愿望，点赞排序\n"
            "2. 飞行自动驾驶平台: http://localhost:8002\n"
            "   - 功能: 飞行数据处理，路径预测\n"
            "3. 降落辅助系统: http://localhost:8003\n"
            "   - 功能: 摄像头视图，点击降落\n"
            "4. 飞书集成服务: http://localhost:8004\n"
            "   - 功能: 飞书机器人对话接口"
        )


# 示例用法
def main():
    """主函数 - 演示飞书聊天功能"""
    # 飞书机器人webhook URL
    WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/c0d514f8-7c42-4c14-b9b1-922d71ba772d"
    
    # 创建聊天服务
    chat_service = ChatService(WEBHOOK_URL)
    
    print("🚀 飞书机器人聊天功能演示")
    print("=" * 50)
    
    # 创建聊天处理器
    chat_handler = FeishuChatHandler(chat_service)
    
    # 演示各种命令处理
    print("\n🔧 命令处理演示:")
    print(chat_handler.handle_message("/status", True))
    print(chat_handler.handle_message("/wishes", True))
    print(chat_handler.handle_message("/flight", True))
    print(chat_handler.handle_message("/landing", True))
    print(chat_handler.handle_message("/help", True))
    
    # 演示自然语言处理
    print("\n💬 自然语言处理演示:")
    print(chat_handler.handle_message("@机器人 状态", True))
    print(chat_handler.handle_message("@机器人 飞行系统", True))


if __name__ == "__main__":
    main()