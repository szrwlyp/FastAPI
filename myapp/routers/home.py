from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os


router = APIRouter()


# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 计算模板目录路径（假设 templates 在项目根目录）
templates_dir = os.path.join(current_dir, "../templates")

# 初始化模板引擎
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", summary="首页")
async def home_page(request: Request):
    # 渲染模板并传递数据
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": "FastAPI 首页",
        },
    )
