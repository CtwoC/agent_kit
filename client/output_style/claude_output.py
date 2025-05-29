# claude_output.py
import asyncio
import json
import os
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from typing import List, Dict, Any

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# 初始化客户端
client = AsyncAnthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    base_url=os.getenv('ANTHROPIC_API_URL', 'https://api.anthropic.com')
)

# 获取模型名称
MODEL_NAME = os.getenv('CLAUDE_MODEL', 'claude-3-opus-20240229')

async def non_streaming_chat() -> Dict[str, Any]:
    """非流式对话示例"""
    response = await client.messages.create(
        model=MODEL_NAME,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": "Tell me a short joke."
        }],
        temperature=0.7,
    )
    return response.model_dump()

async def streaming_chat() -> List[Dict[str, Any]]:
    """流式对话示例"""
    chunks = []
    stream = await client.messages.create(
        model=MODEL_NAME,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": "Count from 1 to 5 slowly."
        }],
        temperature=0.7,
        stream=True
    )
    async for chunk in stream:
        chunks.append(chunk.model_dump())
    return chunks

async def tool_call_chat() -> Dict[str, Any]:
    """工具调用示例"""
    response = await client.messages.create(
        model=MODEL_NAME,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": "What's the weather like in Shanghai?"
        }],
        temperature=0.7,
        tools=[{
            "type": "custom",
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }]
    )
    return response.model_dump()

async def streaming_tool_call_chat() -> List[Dict[str, Any]]:
    """流式工具调用示例"""
    chunks = []
    stream = client.messages.stream(
        model=MODEL_NAME,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": "What's the weather like in Shanghai?"
        }],
        temperature=0.7,
        tools=[{
            "type": "custom",
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }]
    )
    async with stream as response:
        async for chunk in response:
            chunks.append(chunk.model_dump())
    return chunks

async def main():
    # 检查API密钥
    if not os.getenv('ANTHROPIC_API_KEY'):
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
    # # 非流式响应
    # print("\n=== Non-Streaming Response ===")
    # response = await non_streaming_chat()
    # print(json.dumps(response, indent=2))
    
    # # 流式响应
    # print("\n=== Streaming Response ===")
    # chunks = await streaming_chat()
    # print(json.dumps(chunks, indent=2))
    
    # # 工具调用响应
    # print("\n=== Tool Call Response ===")
    # tool_response = await tool_call_chat()
    # print(json.dumps(tool_response, indent=2))
    
    # 流式工具调用响应
    print("\n=== Streaming Tool Call Response ===")
    stream_chunks = await streaming_tool_call_chat()
    print(json.dumps(stream_chunks, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
