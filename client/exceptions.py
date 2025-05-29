"""LLM 客户端异常定义"""

class LLMError(Exception):
    """基础 LLM 异常"""
    pass

class StreamTimeoutError(LLMError):
    """流式响应超时异常"""
    pass
