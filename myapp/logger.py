# logger.py
from loguru import logger
import sys

# 移除默认的日志处理器
logger.remove()

# 添加终端输出（带颜色）
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 可选：添加日志文件输出
logger.add("logs/fastapi.log", rotation="500 MB", level="DEBUG")

# 导出 logger 实例
__all__ = ["logger"]