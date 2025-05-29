import os
import asyncio
from typing import Dict, Any
from client.base_client import BaseLLMClient, Tool
from client.claude_client import ClaudeClient

async def print_stream_chunks(chunks: Dict[str, Any]):
    """打印流式输出的内容"""
    for chunk in chunks:
        if "content" in chunk:
            for content in chunk["content"]:
                if content["type"] == "text":
                    print(content["text"], end="", flush=True)
                elif content["type"] == "tool_use":
                    print(f"\n[调用工具] {content['name']}")
                    print(f"参数: {content['input']}")
        
async def main():
    # 从环境变量获取 API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
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
