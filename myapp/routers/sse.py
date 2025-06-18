from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime

from ..logger import logger

import os

router = APIRouter()

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 计算模板目录路径（假设 templates 在项目根目录）
templates_dir = os.path.join(current_dir, "../templates")

# 初始化模板引擎
templates = Jinja2Templates(directory=templates_dir)


@router.get("/ssePage", summary="sse")
async def sse_page(request: Request):

    # 渲染模板并传递数据
    return templates.TemplateResponse(
        "sse.html",
        {
            "request": request,
            "page_title": "FastAPI 首页",
        },
    )


# 精简版 SSE 事件生成器
async def simple_sse_generator(request: Request):
    count = 0
    try:
        while True:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                break

            count += 1
            # 创建事件数据
            event_data = {
                "count": count,
                "time": datetime.now().isoformat(),
                "message": f"Server message #{count}",
            }

            # 转换为 SSE 格式
            # 格式: data: {json}\n\n
            yield f"data: {json.dumps(event_data)}\n\n"

            # 每秒发送一次
            await asyncio.sleep(10)

        logger.error(f"Client disconnected")
    finally:
        logger.info(f"SSE stream ended")


# SSE 路由
@router.get("/sse")
async def sse_endpoint(request: Request):
    # 获取客户端通过GET方法传过来的参数
    logger.info(request.query_params.get("user_id"))
    return StreamingResponse(
        content=simple_sse_generator(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
