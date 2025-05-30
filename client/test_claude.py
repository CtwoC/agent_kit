import os
import asyncio
from typing import Dict, Any
from claude_client import ClaudeClient

async def print_stream_chunks(chunk: Dict[str, Any]):
    """打印流式输出的内容"""
    # 首先打印chunk的类型
    chunk_type = chunk.get("type", "unknown")
    
    # 根据不同的类型进行处理
    if chunk_type == "text":
        # 如果是文本类型，直接打印text字段
        if "text" in chunk:
            print(chunk["text"], end="", flush=True)
    elif chunk_type == "content_block_delta":
        # 如果是content_block_delta类型，检查delta中的内容
        if "delta" in chunk:
            delta = chunk["delta"]
            if delta.get("type") == "text_delta" and "text" in delta:
                print(delta["text"], end="", flush=True)
    elif chunk_type == "message_start":
        # 消息开始，可以忽略
        pass
    elif chunk_type == "content_block_start":
        # 内容块开始，可以忽略
        pass
    elif chunk_type == "content_block_stop":
        # 内容块结束，可以忽略
        pass
    elif chunk_type == "message_delta":
        # 消息更新，可以忽略
        pass
    else:
        # 其他类型的chunk，打印类型信息
        print(f"[{chunk_type}]", end="", flush=True)
        
async def main():
    # 从环境变量获取 API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"DEBUG: API key 前8位: {api_key[:8] if api_key else 'None'}")  # 添加调试信息
    if not api_key:
        raise ValueError("请设置环境变量 ANTHROPIC_API_KEY")
        
    # 初始化客户端
    mcp_url = "http://39.103.228.66:8165/mcp"
    
    async with ClaudeClient(api_key=api_key, mcp_urls=[mcp_url]) as client:
        # 测试简单对话
        print("\n=== 测试简单对话 ===")
        async for chunk in client.chat_stream("1850401804 + 1808190385 等于多少？"):
            await print_stream_chunks(chunk)
            
        # 测试工具调用
        print("\n\n=== 测试工具调用 ===")
        async for chunk in client.chat_stream("帮我给 Bob 打个招呼"):
            await print_stream_chunks(chunk)
            
if __name__ == "__main__":
    asyncio.run(main())
