import os
import asyncio
from typing import Dict, Any
from claude_client import ClaudeClient

async def print_stream_chunks(chunk: Dict[str, Any]):
    """打印流式输出的内容"""
    print(f"DEBUG: 收到chunk: {chunk}")  # 添加调试信息
    if "content" in chunk:
        print(f"DEBUG: chunk包含content字段: {chunk['content']}")  # 添加调试信息
        if isinstance(chunk["content"], list):
            for content in chunk["content"]:
                print(f"DEBUG: 处理content: {content}")  # 添加调试信息
                if content["type"] == "text":
                    print(content["text"], end="", flush=True)
                elif content["type"] == "tool_use":
                    print(f"\n[调用工具] {content['name']}")
                    print(f"参数: {content['input']}")
        elif isinstance(chunk["content"], str):
            print(chunk["content"], end="", flush=True)
        
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
