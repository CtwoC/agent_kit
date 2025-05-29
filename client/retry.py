"""重试装饰器"""
import asyncio
from functools import wraps
from typing import Type, Tuple
from exceptions import StreamTimeoutError

def async_retry(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_exceptions: Tuple[Type[Exception], ...] = (StreamTimeoutError,),
    backoff_factor: float = 2.0
):
    """异步重试装饰器
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        retry_exceptions: 需要重试的异常类型
        backoff_factor: 退避因子，每次重试延迟时间会乘以这个因子
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = retry_delay * (backoff_factor ** attempt)
                        print(f"Retrying after {delay}s... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                    continue
            raise last_exception
        return wrapper
    return decorator
