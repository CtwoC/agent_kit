#!/usr/bin/env python3
"""
聊天处理模块 - 负责聊天逻辑处理
包括prompt组合、OpenAI客户端创建、流式响应处理
"""

import sys
import os
import json
import asyncio
from typing import Optional, AsyncGenerator

# 添加client目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
client_path = os.path.join(project_root, 'client')
sys.path.insert(0, client_path)

from openai_client import OpenAIClient

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """你是一个智能AI助手，能够帮助用户解答问题、提供信息和协助完成任务。你有以下特点：

1. 友善且专业的交流方式
2. 能够使用可用的工具来辅助回答问题
3. 提供准确、有用的信息
4. 根据上下文给出恰当的回应

请用中文与用户交流，保持简洁明了的回答风格。"""

class ChatProcessor:
    """聊天处理器"""
    
    @staticmethod
    def create_client() -> OpenAIClient:
        """
        创建新的OpenAI客户端
        
        Returns:
            OpenAIClient: 配置好的OpenAI客户端实例
            
        Raises:
            ValueError: 如果环境变量未设置
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ 请设置环境变量 OPENAI_API_KEY")
        
        mcp_url = os.getenv("MCP_URL", "http://39.103.228.66:8165/mcp/")
        base_url = os.getenv("OPENAI_BASE_URL", "http://43.130.31.174:8003/v1")
        
        return OpenAIClient(
            api_key=api_key,
            base_url=base_url,
            mcp_urls=[mcp_url] if mcp_url else None
        )
    
    @staticmethod
    def build_prompt(message: str, system_prompt: Optional[str] = None) -> str:
        """
        构建完整的prompt
        
        Args:
            message: 用户消息
            system_prompt: 可选的自定义系统提示词
            
        Returns:
            str: 组合后的完整prompt
        """
        system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        return f"系统提示词：\n{system_prompt}\n\n用户消息：\n{message}"
    
    @staticmethod
    async def process_stream_chat(
        message: str, 
        uid: str, 
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        处理流式聊天请求
        
        Args:
            message: 用户消息
            uid: 用户ID
            system_prompt: 可选的自定义系统提示词
            
        Yields:
            str: 流式响应数据（JSON格式）
        """
        client = None
        try:
            print(f"📝 用户 {uid} 开始流式处理: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # 创建并初始化客户端
            client = ChatProcessor.create_client()
            await client.__aenter__()
            
            # 构建prompt
            full_prompt = ChatProcessor.build_prompt(message, system_prompt)
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成响应...', 'uid': uid}, ensure_ascii=False)}\n\n"
            
            # 处理流式响应
            content_buffer = ""
            async for chunk in client.stream_chat(full_prompt):
                chunk_type = chunk.get("type", "")
                
                # 处理文本内容的增量更新
                if chunk_type == "response.output_text.delta":
                    delta_text = chunk.get("delta", "")
                    if delta_text:
                        content_buffer += delta_text
                        yield f"data: {json.dumps({'type': 'content', 'chunk': delta_text, 'uid': uid}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.01)  # 流式效果延迟
                
                # 处理工具调用开始
                elif chunk_type == "response.output_item.added":
                    item = chunk.get("item", {})
                    if item.get("type") == "function_call":
                        function_name = item.get("name", "unknown")
                        print(f"🔧 用户 {uid} 调用工具: {function_name}")
                        yield f"data: {json.dumps({'type': 'tool_call', 'tool': function_name, 'status': 'started', 'uid': uid}, ensure_ascii=False)}\n\n"
                
                # 处理工具调用完成
                elif chunk_type == "response.output_item.done":
                    item = chunk.get("item", {})
                    if item.get("type") == "function_call" and item.get("status") == "completed":
                        function_name = item.get("name", "unknown")
                        arguments = item.get("arguments", "{}")
                        print(f"✅ 用户 {uid} 工具完成: {function_name}")
                        yield f"data: {json.dumps({'type': 'tool_call', 'tool': function_name, 'status': 'completed', 'arguments': arguments, 'uid': uid}, ensure_ascii=False)}\n\n"
                
                # 处理响应创建
                elif chunk_type == "response.created":
                    yield f"data: {json.dumps({'type': 'thinking', 'message': '正在思考...', 'uid': uid}, ensure_ascii=False)}\n\n"
                
                # 处理内容部分添加
                elif chunk_type == "response.content_part.added":
                    yield f"data: {json.dumps({'type': 'content_start', 'message': '开始生成内容...', 'uid': uid}, ensure_ascii=False)}\n\n"
            
            # 发送完成事件和统计信息
            completion_data = {
                "type": "complete",
                "full_content": content_buffer,
                "uid": uid,
                "usage": {
                    "input_tokens": client.usage.input_tokens,
                    "output_tokens": client.usage.output_tokens,
                    "total_tokens": client.usage.total_tokens,
                    "total_cost": round(client.usage.total_cost, 6)
                }
            }
            yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
            
            print(f"✅ 用户 {uid} 流式响应完成，总计 {client.usage.total_tokens} tokens")
            
        except Exception as e:
            print(f"❌ 用户 {uid} 处理流式请求时发生错误: {str(e)}")
            error_data = {
                "type": "error",
                "error": f"处理请求时发生错误: {str(e)}",
                "uid": uid
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        finally:
            # 确保关闭客户端
            if client:
                try:
                    await client.__aexit__(None, None, None)
                except Exception as e:
                    print(f"⚠️ 关闭客户端时发生错误: {str(e)}")
    
    @staticmethod
    async def process_chat(
        message: str, 
        uid: str, 
        system_prompt: Optional[str] = None
    ) -> dict:
        """
        处理非流式聊天请求
        
        Args:
            message: 用户消息
            uid: 用户ID
            system_prompt: 可选的自定义系统提示词
            
        Returns:
            dict: 包含响应内容和统计信息的字典
            
        Raises:
            Exception: 处理过程中的各种异常
        """
        client = None
        try:
            print(f"📝 用户 {uid} 开始非流式处理: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # 创建并初始化客户端
            client = ChatProcessor.create_client()
            await client.__aenter__()
            
            # 构建prompt
            full_prompt = ChatProcessor.build_prompt(message, system_prompt)
            
            # 调用OpenAI客户端
            response = await client.chat(full_prompt)
            
            # 提取响应内容
            assistant_message = response["choices"][0]["message"]["content"]
            
            # 构建响应
            chat_response = {
                "response": assistant_message,
                "uid": uid,
                "usage": {
                    "input_tokens": client.usage.input_tokens,
                    "output_tokens": client.usage.output_tokens,
                    "total_tokens": client.usage.total_tokens,
                    "total_cost": round(client.usage.total_cost, 6)
                },
                "model": response.get("model", "unknown"),
                "type": "non_stream"
            }
            
            print(f"✅ 用户 {uid} 非流式响应完成，总计 {client.usage.total_tokens} tokens")
            
            return chat_response
            
        finally:
            # 确保关闭客户端
            if client:
                try:
                    await client.__aexit__(None, None, None)
                except Exception as e:
                    print(f"⚠️ 关闭客户端时发生错误: {str(e)}") 