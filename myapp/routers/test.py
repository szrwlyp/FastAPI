from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, HTMLResponse
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
  </head>
  <script src="https://unpkg.com/petite-vue" defer init></script>

  <body>
    <div id="messages"></div>
    <script>
      // const evtSource = new EventSource("http://127.0.0.1:8000/test/sse");
      // evtSource.onmessage = function (event) {
      //   console.log(event.data);

      //   if (event.data === "[DONE]") {
      //     evtSource.close();
      //     return false;
      //   }

      //   document.getElementById("messages").innerText += event.data;
      // };
      async function askQuestion(question) {
        const response = await fetch("http://127.0.0.1:8000/test/sse", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: question }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 获取响应体的 readable stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let done = false;
        while (!done) {
          const { value, done: readDone } = await reader.read();
          done = readDone;

          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            const sliceChunk = chunk.slice(5).replace(/\\n/g, '');

            if (sliceChunk !== "[DONE]") {
              // 处理接收到的数据块
              document.getElementById("messages").innerHTML += `${sliceChunk}`;
            }
          }
        }
        console.log("Stream complete");
      }

      // 调用函数示例
      askQuestion("What is the weather like today?");
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
        await asyncio.sleep(1)

    # 最后一条消息后发送完成信号
    yield {"event": "complete", "data": "[DONE]"}


@router.post("/test/sse")
async def sse(request: Request):
    """ "
    SSE端点，向客户端推送设备更新状态
    """

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
