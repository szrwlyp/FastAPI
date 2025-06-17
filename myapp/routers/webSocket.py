from fastapi import APIRouter,WebSocket,Query,WebSocketDisconnect,Request
from .connection_manager import ConnectionManager  # 导入连接管理器
from fastapi.templating import Jinja2Templates
import os
import time
import asyncio
import json

from ..logger import logger #日志

router = APIRouter()


manager = ConnectionManager()  # 创建连接管理器实例

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    username: str = Query(..., description="用户唯一标识")
):
    """
    WebSocket 聊天端点
    - username: 用户唯一标识（字符串）
    """
    # 连接用户
    await manager.connect(username, websocket)
    logger.info(f"用户 {username} 已连接")
    
    # 启动心跳任务
    # heartbeat_task = asyncio.create_task(manager.heartbeat(username))
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
        
            # 处理心跳响应
            if data.get("type") == "ping":
                # 发送pong响应
                await websocket.send_json({
                    "type": "pong",
                    "name": "system",
                    "target_user": username,
                    "message_content": "",
                    "timestamp": time.time()
                })
                continue
            
            logger.debug(f"收到来自 {username} 的消息: {data}")
            
            # 更新用户活跃时间
            manager.last_active[username] = time.time()

            # 添加发送者信息
            data["name"] = username
            data["timestamp"] = time.time()
            
            # 发送消息给目标用户
            success = await manager.send_message(data)
            
            if not success:
                # 如果目标用户不在线，通知发送者
                await websocket.send_json({
                    "type": "error",
                    "name": "system",
                    "target_user": username,
                    "message_content": f"用户 {data['target_user']} 不在线",
                    "timestamp": time.time()
                })
                
    except WebSocketDisconnect:
        # 7. 处理断开连接
        await manager.disconnect(username)
        logger.info(f"用户 {username} 已断开连接")
    except Exception as e:
        logger.error(f"用户 {username} 连接异常: {e}")
        await manager.disconnect(username)
    finally:
        # 取消心跳任务
        # heartbeat_task.cancel()
        logger.info(f"用户 {username} 的心跳任务已停止")


@router.websocket("/im")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:

        await asyncio.sleep(3)
        await websocket.send_text(json.dumps({
            "type": "test",
            "name": "lanyuping",
            "target" : "lisi",
            "content": 'aaa',
        }))
        # 每秒钟发送一次数据
        data = await websocket.receive_text()
        logger.info(f"Message received: {data}")  # 打印接收到的数据
        # await websocket.send_text(f"Message text was: {data}")



# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 计算模板目录路径（假设 templates 在项目根目录）
templates_dir = os.path.join(current_dir, "../templates")

# 初始化模板引擎
templates = Jinja2Templates(directory=templates_dir)

@router.get('/webSocketPage',summary='webSocket')
async def home_page(request: Request):
    # 渲染模板并传递数据
    return templates.TemplateResponse(
        "webSocket.html",{
            "request": request,
            "page_title": "FastAPI 首页",
        }
    )

