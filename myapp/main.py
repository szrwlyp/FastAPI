from fastapi import FastAPI
from .routers import home,webSocket,users, test, fileUpload,emailModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
import os.path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, HTMLResponse


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
app.include_router(home.router)
app.include_router(webSocket.router)
app.include_router(users.router)
app.include_router(test.router)
app.include_router(fileUpload.router)
app.include_router(emailModel.router)
# app.include_router(chat.router) //大模型


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, debug=True, reload=True)
