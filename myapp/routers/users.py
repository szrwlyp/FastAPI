from fastapi import FastAPI, APIRouter, HTTPException, Path
from pydantic import BaseModel, HttpUrl
from typing import List
from ..logger import logger #日志
router = APIRouter()


@router.get("/users/me", tags=["用户"], summary="获取当前用户信息")
async def read_user_me():
    """
    获取当前用户基本信息
    """
    return {"user_id": "the current user"}


@router.get("/users/{user_id}", tags=["用户"], summary="根据用户ID获取用户信息")
async def read_user(user_id: int = Path(description="用户ID")):
    """
    通过用户ID获取用户基本信息
    """
    return {"user_id": user_id}


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    # tags: List[str] = []
    tags: set[str] = set()
    # images: Image | None = None
    images: list[Image] | None = None


class User(BaseModel):
    username: str
    full_name: str | None = None


@router.post("/items/")
async def read_item(item: Item, user: User):
    """
        {
        "item": {
            "name": "Foo",
            "description": "The pretender",
            "price": 42.0,
            "tax": 3.2,
            "tags": [
                "222",
                "111",
                "222"
            ],
            "images": [{
                "url": "http://example.com/baz.jpg",
                "name": "ffff"
            }]
        },
        "user": {
            "username": "张三",
            "full_name": "测试"
        }
    }
    """
    return item


@router.post("/items/multiple", tags=["用户"], summary="图片列表")
async def create_multiple_images(images: list[Image]):
    """
        [
        {
            "url": "http://example.com/baz.jpg",
            "name": "ffff"
        }
    ]
    """

    for image in images:
        logger.info(image.name)
    return images
