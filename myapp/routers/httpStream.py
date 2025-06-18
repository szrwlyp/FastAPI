from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
import os
import asyncio
import random
from ..logger import logger  # 日志

router = APIRouter()


# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 计算模板目录路径（假设 templates 在项目根目录）
templates_dir = os.path.join(current_dir, "../templates")

# 初始化模板引擎
templates = Jinja2Templates(directory=templates_dir)


@router.get("/http_stream_page", summary="http_stream")
async def home_page(request: Request):
    # 渲染模板并传递数据
    return templates.TemplateResponse(
        "httpStream.html",
        {
            "request": request,
            "page_title": "FastAPI 首页",
        },
    )


async def event_generator():
    # 模拟发送的数据
    messages = ["Hello", " from", " simulated", " ChatGPT!"]

    for msg in messages:
        yield {"event": "message", "data": msg}
        # 模拟延迟
        await asyncio.sleep(3)

    # 最后一条消息后发送完成信号
    yield {"event": "complete", "data": "[DONE]"}


class sseItem(BaseModel):
    question: str


@router.post("/http_stream")
async def sse(request: Request):
    """ "
    SSE端点，向客户端推送设备更新状态
    """

    try:
        json_data = await request.json()

        sse_data = sseItem(**json_data)  # 自动校验并转换为对象
        logger.info(f"打印json数据：{sse_data.question}")
    except Exception as e:
        logger.error(f"JSON Data Error:{e}")  # 如果不是 JSON 类型会报错

    async def event_stream():
        try:
            async for event_dict in event_generator():
                if await request.is_disconnected():
                    break
                yield f"data:{event_dict['data']}\n\n"
                # if event_dict["event"] == "complete":
                #     break
        except asyncio.CancelledError as e:
            logger.error(f"SSE connection was closed by the client.")
            logger.info(f"{e}")
            raise e

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
