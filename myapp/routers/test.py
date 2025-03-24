from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
import json
import asyncio

router = APIRouter()


@router.get("/test/sse/html", response_class=HTMLResponse)
async def sse_html():
    return """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>SSE Test</title>
    <style>
      [v-cloak] {
        display: none !important;
      }
      .input-item {
        display: flex;
      }

      .send {
        padding: 0 10px;
        cursor: pointer;
      }
    </style>
  </head>

  <body>
    <div v-scope class="">
      <div class="input-item">
        <input type="text" v-model="sseInput" class="input" />
        <div class="send" @click="sendSSE">发送</div>
        <div class="send" @click="cancelSSE">取消</div>
      </div>
      <div class="message" v-cloak>{{sseMessage}}</div>
    </div>
    <script type="module">
      import { createApp } from "https://unpkg.com/petite-vue?module";
      createApp({
        sseMessage: "",
        sseInput: "",
        // fetchInstance: null,
        controller: new AbortController(),
        async sendSSE() {
          const fetchInstance = await fetch("http://127.0.0.1:8000/test/sse", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ question: this.sseInput }),
            signal: this.controller.signal,
          });

          if (!fetchInstance.ok) {
            throw new Error(`HTTP error! status: ${fetchInstance.status}`);
          }

          // 获取响应体的 readable stream
          const reader = fetchInstance.body.getReader();
          const decoder = new TextDecoder("utf-8");

          let done = false;
          while (!done) {
            const { value, done: readDone } = await reader.read();
            done = readDone;

            if (value) {
              const chunk = decoder.decode(value, { stream: true });
              const sliceChunk = chunk.slice(5).replace(/\\n/g, "");
              if (sliceChunk.trim() !== "[DONE]") {
                // 处理接收到的数据块
                this.sseMessage += sliceChunk;
              }
            }
          }
          console.log("Stream complete");
        },

        cancelSSE() {
          // 取消请求
          this.controller.abort();
        },
      }).mount();
    </script>
  </body>
</html>

    """


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


@router.post("/test/sse")
async def sse(request: Request):
    """ "
    SSE端点，向客户端推送设备更新状态
    """

    try:
        json_data = await request.json()
        print("JSON Data:", sseItem(**json_data).question)
    except Exception as e:
        print("JSON Data Error:", str(e))  # 如果不是 JSON 类型会报错

    async def event_stream():
        try:
            async for event_dict in event_generator():
                if await request.is_disconnected():
                    break
                yield f"data:{event_dict['data']}\n\n"
                # if event_dict["event"] == "complete":
                #     break
        except asyncio.CancelledError as e:
            print("SSE connection was closed by the client.")
            print(e)
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
