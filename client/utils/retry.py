"""重试装饰器"""
import asyncio
import functools
from typing import TypeVar, Callable, Any, Optional, AsyncIterator

T = TypeVar('T')
StreamT = TypeVar('StreamT')

def async_retry(
    max_retries: int = 3,
    timeout: float = 60.0,  # 默认60s超时
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """普通异步重试装饰器
    
    Args:
        max_retries: 最大重试次数
        timeout: 整体超时时间（秒）
        
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # 使用超时运行函数
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                    return result
                    
                except asyncio.TimeoutError:
                    last_error = asyncio.TimeoutError(
                        f"Timeout after {timeout}s (attempt {attempt + 1}/{max_retries})"
                    )
                    print(f"WARNING: {last_error}")
                    continue
                    
                except Exception as e:
                    raise e
                    
            if last_error:
                raise last_error
                
        return wrapper
    return decorator

def mcp_tool_retry(
    max_retries: int = 3,
    timeout: float = 15.0,  # 单次调用超时
    backoff_delay: float = 1.0,  # 重试延迟基数
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """MCP工具调用专用重试装饰器
    
    Args:
        max_retries: 最大重试次数
        timeout: 单次调用超时时间（秒）
        backoff_delay: 重试延迟基数（秒），实际延迟为 backoff_delay * attempt
        
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        delay = backoff_delay * attempt
                        print(f"DEBUG: MCP重试延迟 {delay}s (第{attempt + 1}次尝试)")
                        await asyncio.sleep(delay)
                    
                    # 使用超时运行函数
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                    
                    if attempt > 0:
                        print(f"DEBUG: MCP重试成功 (第{attempt + 1}次尝试)")
                    
                    return result
                    
                except asyncio.TimeoutError as e:
                    last_error = asyncio.TimeoutError(
                        f"MCP调用超时 {timeout}s (第{attempt + 1}/{max_retries}次尝试)"
                    )
                    print(f"WARNING: {last_error}")
                    if attempt == max_retries - 1:
                        break
                    continue
                    
                except Exception as e:
                    # 对于网络连接错误等，可以重试
                    error_types_to_retry = [
                        'ConnectionError',
                        'TimeoutError', 
                        'ConnectionRefusedError',
                        'NetworkError',
                        'HTTPError',
                        'ConnectTimeout',
                        'ReadTimeout',
                        'WriteTimeout',
                        'ReadError',  # 读取错误
                        'WriteError',  # 写入错误
                        'IOError',  # IO错误
                        'OSError',  # 操作系统错误
                        'BrokenResourceError',  # MCP资源损坏错误
                        'ResourceUnavailableError',  # MCP资源不可用
                        'ProtocolError',  # 协议错误
                        'StreamError',  # 流错误
                        'ClientError',  # 客户端错误
                        'ServerError',  # 服务器错误
                        'TransportError',  # 传输错误
                        'MCPError',  # MCP通用错误
                        'SocketError',  # Socket错误
                        'SSLError',  # SSL错误
                        'BadRequestError',  # 坏请求错误（可能是临时的）
                        'RequestTimeoutError',  # 请求超时
                        'ResponseTimeoutError',  # 响应超时
                        'EndOfStream',  # 流结束错误
                        'StreamClosedError',  # 流关闭错误
                        'ResourceError'  # 资源错误
                    ]
                    
                    # 检查错误类型名称
                    error_type_name = type(e).__name__
                    should_retry = any(error_type in error_type_name for error_type in error_types_to_retry)
                    
                    # 也检查错误消息中是否包含关键词
                    error_message = str(e).lower()
                    retry_keywords = [
                        'connection', 'timeout', 'network', 'broken', 'unavailable',
                        'protocol', 'transport', 'reset', 'refused', 'unreachable'
                    ]
                    message_suggests_retry = any(keyword in error_message for keyword in retry_keywords)
                    
                    if should_retry or message_suggests_retry:
                        last_error = e
                        print(f"WARNING: MCP连接错误，尝试重试 (第{attempt + 1}/{max_retries}次)")
                        print(f"  错误类型: {error_type_name}")
                        print(f"  错误信息: {str(e)}")
                        if attempt == max_retries - 1:
                            break
                        continue
                    else:
                        # 其他类型的错误直接抛出，不重试
                        print(f"ERROR: 不可重试的错误类型: {error_type_name}: {str(e)}")
                        raise e
                    
            # 所有重试都失败了
            if last_error:
                raise last_error
                
        return wrapper
    return decorator

def stream_async_retry(
    max_retries: int = 3,
    chunk_timeout: float = 30.0,  # 默认30s chunk超时
) -> Callable[[Callable[..., AsyncIterator[StreamT]]], Callable[..., AsyncIterator[StreamT]]]:
    """流式异步重试装饰器
    
    Args:
        max_retries: 最大重试次数
        chunk_timeout: chunk间隔超时时间（秒）
        
    Returns:
        装饰后的函数
    """
    def decorator(
        func: Callable[..., AsyncIterator[StreamT]]
    ) -> Callable[..., AsyncIterator[StreamT]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[StreamT]:
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    stream = func(*args, **kwargs)
                    
                    while True:
                        try:
                            # 使用wait_for对获取下一个chunk进行超时控制
                            chunk = await asyncio.wait_for(stream.__anext__(), chunk_timeout)
                            yield chunk
                            
                        except StopAsyncIteration:
                            # 流正常结束
                            return
                            
                        except asyncio.TimeoutError:
                            raise asyncio.TimeoutError(
                                f"Timeout waiting for next chunk after {chunk_timeout}s"
                            )
                    
                except asyncio.TimeoutError as e:
                    last_error = e
                    print(f"WARNING: {e} (attempt {attempt + 1}/{max_retries})")
                    continue
                    
                except Exception as e:
                    raise e
                    
            if last_error:
                raise last_error
                
        return wrapper
    return decorator

