from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

import torch, torchvision


router = APIRouter()

# print(torch.__version__)  # 应输出 2.2.1 或 2.7.0
# print(torchvision.__version__)  # 应输出 0.17.1 或 0.18.0

import os

os.environ["BITSANDBYTES_NOWELCOME"] = "1"
os.environ["BITSANDBYTES_CPU_ONLY"] = "1"  # 强制使用CPU
# --- 模型加载 ---
MODEL_NAME = "C:\companyProject\deepseek-llm-7b-base"  # 替换为你的模型路径
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="cpu",  # 自动分配GPU/CPU
    # torch_dtype=torch.float16,  # 半精度减少显存占用
    load_in_4bit=True,  # 4bit量化 (可选)
)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)


# --- 请求体定义 ---
class QueryRequest(BaseModel):
    prompt: str
    max_length: int = 512
    temperature: float = 0.7


# --- API端点 ---
@router.post("/generate")
async def generate_text(request: QueryRequest):
    try:
        response = pipe(
            request.prompt,
            max_length=request.max_length,
            temperature=request.temperature,
            pad_token_id=tokenizer.eos_token_id,  # 防止生成中断
        )
        return {"result": response[0]["generated_text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
