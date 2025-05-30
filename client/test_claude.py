import os
import asyncio
from typing import Dict, Any
from claude_client import ClaudeClient

async def print_stream_chunks(chunk: Dict[str, Any]):
    """打印流式输出的内容
    
    Claude API 的流式响应中，文本内容有两种传递方式：
    1. type="text" 的 chunk：完整的文本块，包含 snapshot
    2. type="content_block_delta" 的 chunk：增量更新，只包含新增的文本
    
    我们选择只处理第二种，因为它能提供更细节的增量更新。
    """
    chunk_type = chunk.get("type", "unknown")
    
    # 只处理三种主要类型
    if chunk_type == "content_block_delta":
        # 如果是content_block_delta类型，检查delta中的内容
        if "delta" in chunk:
            delta = chunk["delta"]
            if delta.get("type") == "text_delta" and "text" in delta:
                # 打印增量更新的文本
                print(delta["text"], end="", flush=True)
    elif chunk_type == "tool_use":
        # 如果是工具调用
        content_block = chunk.get("content_block", {})
        print(f"\n[调用工具] {content_block.get('name', 'unknown')}")
        print(f"参数: {content_block.get('input', {})}")
    elif chunk_type not in ["message_start", "content_block_start", "content_block_stop", "message_delta"]:
        # 其他非常规类型才打印类型信息
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
