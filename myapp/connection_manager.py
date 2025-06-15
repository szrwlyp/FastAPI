import asyncio
import json
import time
from typing import Dict, List, Optional
from fastapi import WebSocket

class ConnectionManager:
    """
    一对一 WebSocket 聊天连接管理器
    管理用户连接和消息转发
    """
    
    def __init__(self):
        # 存储用户连接 {username: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储用户最后活跃时间 {username: timestamp}
        self.last_active: Dict[str, float] = {}
        # 存储离线消息 {username: [message_dict]}
        self.offline_messages: Dict[str, List[dict]] = {}

    async def connect(self, username: str, websocket: WebSocket):
        """接受新连接并关联用户"""
        await websocket.accept()
        self.active_connections[username] = websocket
        self.last_active[username] = time.time()
        print(f"用户 {username} 已连接")
        
        # 发送离线消息
        await self._deliver_offline_messages(username)
        
        return True

    async def disconnect(self, username: str):
        """处理连接断开"""
        if username in self.active_connections:
            del self.active_connections[username]
        if username in self.last_active:
            del self.last_active[username]
        print(f"用户 {username} 已断开")
        return True

    async def send_message(self, message: dict) -> bool:
        """
        发送消息给指定用户
        - message: 消息字典，包含 type, name, target_user, message_content
        - 返回: True 发送成功, False 用户不在线
        """
        target_user = message.get("target_user")
        
        if not target_user:
            return False
            
        if target_user in self.active_connections:
            try:
                # 更新接收者活跃时间
                self.last_active[target_user] = time.time()
                
                # 发送消息
                await self.active_connections[target_user].send_json(message)
                return True
            except Exception as e:
                print(f"发送消息给 {target_user} 失败: {e}")
                # 连接已失效
                await self.disconnect(target_user)
                return False
        else:
            # 用户不在线，存储离线消息
            if target_user not in self.offline_messages:
                self.offline_messages[target_user] = []
            self.offline_messages[target_user].append(message)
            print(f"用户 {target_user} 不在线，已存储离线消息")
            return False

    async def get_online_users(self) -> list:
        """获取当前在线用户列表"""
        return list(self.active_connections.keys())
    
    async def is_user_online(self, username: str) -> bool:
        """检查用户是否在线"""
        return username in self.active_connections
    
    async def _deliver_offline_messages(self, username: str):
        """发送用户的离线消息"""
        if username in self.offline_messages and self.offline_messages[username]:
            print(f"向用户 {username} 发送 {len(self.offline_messages[username])} 条离线消息")
            for message in self.offline_messages.pop(username):
                await self.send_message(message)
    
    async def heartbeat(self, username: str):
        """心跳检测，保持连接活跃"""
        try:
            while True:
                await asyncio.sleep(15)  # 每15秒发送一次心跳
                
                # 检查用户是否仍然连接
                if not await self.is_user_online(username):
                    break
                
                try:
                    # 发送心跳包
                    ping_message = {
                        "type": "ping",
                        "name": "system",
                        "target_user": username,
                        "message_content": "",
                        "timestamp": time.time()
                    }
                    await self.active_connections[username].send_json(ping_message)
                    
                    # 检查是否超时无响应（30秒）
                    if time.time() - self.last_active.get(username, 0) > 30:
                        print(f"用户 {username} 心跳超时，断开连接")
                        await self.disconnect(username)
                        break
                except Exception as e:
                    print(f"用户 {username} 心跳异常: {e}")
                    # 连接已断开
                    await self.disconnect(username)
                    break
        except Exception as e:
            print(f"用户 {username} 心跳任务异常: {e}")