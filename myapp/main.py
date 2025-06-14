from fastapi import FastAPI, WebSocket
from .routers import users, test, fileUpload, chat
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
import uvicorn
import os.path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, HTMLResponse
import asyncio

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

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
app.include_router(chat.router)


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


@app.get("/send_email")
def send_email():
    """
    发送邮件。
    :param subject: 邮件主题
    :param body:邮件正文
    :param recipient:收件人邮箱地址
    """

    # 邮箱配置
    smtp_server = "smtp.163.com"
    smtp_port = 25
    username = "szrwlyp@163.com"
    # password = "szrwlyp0320..."
    password = "RNU4nbqkU3bTEW6J"  # 授权码
    # 接受者
    subject = "Hello from Python!"
    body = "测试测试"
    recipient = "1545763981@qq.com"

    # 创建MIME多部分消息
    message = MIMEText(body, "plain", "utf-8")
    message["From"] = username
    message["To"] = recipient
    message["Subject"] = subject

    try:
        # 创建SMTP对象
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)

        # 发送邮件
        server.sendmail(username, [recipient], message.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败：{e}")
    finally:
        server.quit()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:

        await asyncio.sleep(3)
        await websocket.send_text("Hello, FastAPI!")
        # 每秒钟发送一次数据
        # data = await websocket.receive_text()
        # await websocket.send_text(f"Message text was: {data}")


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, debug=True, reload=True)
