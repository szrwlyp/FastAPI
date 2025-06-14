import os
from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# 临时存储目录配置
TEMP_UPLOAD_DIR = "temp_uploads"
MERGED_DIR = "merged_files"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(MERGED_DIR, exist_ok=True)


router = APIRouter()


@router.post("/upload-chunk/")
async def upload_chunk(
    index: int = Form(...),
    total: int = Form(...),
    fileName: str = Form(...),
    file: UploadFile = File(...),
):

    # 创建分片存储目录
    chunk_dir = os.path.join(TEMP_UPLOAD_DIR)
    os.makedirs(chunk_dir, exist_ok=True)

    # 保存分片
    chunk_path = os.path.join(chunk_dir, f"{index}_{fileName}.dat")
    with open(chunk_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "success", "chunk_index": index}


@router.post("/merge-chunks/")
async def merge_chunks(fileName: str = Form(...), total: int = Form(...)):  # 文件名  # 总分片数
    # 分片存储目录
    chunk_dir = TEMP_UPLOAD_DIR

    # 检查是否所有分片都已上传
    chunks = []
    for i in range(total):
        chunk_file_name = f"{i}_{fileName}.dat"
        chunk_path = os.path.join(chunk_dir, chunk_file_name)
        if not os.path.exists(chunk_path):
            return {"error": f"Chunk {i} is missing."}
        chunks.append(chunk_path)

    # 合并分片
    merged_file_path = os.path.join(MERGED_DIR, fileName)
    with open(merged_file_path, "wb") as outfile:
        for chunk_path in chunks:
            with open(chunk_path, "rb") as infile:
                outfile.write(infile.read())

    # 删除临时分片文件
    for chunk_path in chunks:
        os.remove(chunk_path)

    return {
        "status": "success",
        "message": "File merged successfully.",
        "merged_file_path": merged_file_path,
    }
