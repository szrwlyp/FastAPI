from fastapi import FastAPI, WebSocket,Query,WebSocketDisconnect
from .routers import users, test, fileUpload,emailModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
import uvicorn
import os.path
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, HTMLResponse
import time

from .connection_manager import ConnectionManager  # 导入连接管理器
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi")


app = FastAPI(docs_url=None)

# 挂载静态文件夹
static_file_abspath = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_file_abspath), name="static")


# 自定义 Swagger 文档路由，指向本地的 Swagger UI 文件
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
    )


# 请求验证异常装饰器
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc):
#     return PlainTextResponse(str(exc), status_code=400)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，实际部署时建议指定域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 路由文件
app.include_router(users.router)
app.include_router(test.router)
app.include_router(fileUpload.router)
app.include_router(emailModel.router)
# app.include_router(chat.router) //大模型


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://127.0.0.1:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def root():
    return HTMLResponse(html)
    


manager = ConnectionManager()  # 创建连接管理器实例

@app.websocket("/ws")
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
            logger.debug(f"收到来自 {username} 的消息: {data}")
            
            # 4. 更新用户活跃时间
            manager.last_active[username] = time.time()
            
            # 5. 处理心跳响应
            if data.get("type") == "ping":
                # 发送pong响应
                await websocket.send_json({
                    "type": "ping",
                    "name": "system",
                    "target_user": username,
                    "message_content": "",
                    "timestamp": time.time()
                })
                continue
            
            # 6. 处理聊天消息
            # if data.get("type") == "video-offer" and "target_user" in data and "message_content" in data:
            
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


# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:

#         await asyncio.sleep(3)
#         await websocket.send_text(json.dumps({
#             "type": "test",
#             "name": "lanyuping",
#             "target" : "lisi",
#             "content": 'aaa',
#         }))
#         # 每秒钟发送一次数据
#         data = await websocket.receive_text()
#         print(f"Message received: {data}")  # 打印接收到的数据
#         # await websocket.send_text(f"Message text was: {data}")


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, debug=True, reload=True)
