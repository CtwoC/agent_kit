"""
聊天处理模块
负责AI对话生成、流式内容处理和Redis中转存储
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from utils.logger import get_logger
from utils.status_codes import ChatStatus, create_status_info
from models.api_models import CustomerProfile, CustomerMemory
from storage.redis_client import get_redis_client
from config.settings import get_settings

logger = get_logger(__name__)

class ChatProcessor:
    """聊天处理核心"""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def process(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理AI对话生成
        
        Args:
            enhanced_data: 包含Profile数据的增强请求字典
            
        Returns:
            Dict[str, Any]: 包含处理结果的字典
        """
        uid = enhanced_data.get("uid")
        message = enhanced_data.get("message")
        session_id = enhanced_data.get("session_id") or str(uuid.uuid4())
        
        logger.info(f"💬 开始处理客户对话: {uid}")
        
        # 更新状态
        status_info = create_status_info(
            ChatStatus.PROCESSING,
            message=f"AI正在为客户 {uid} 生成回复",
            progress=0.2
        )
        
        try:
            # 获取Redis客户端用于流式存储
            redis_client = await get_redis_client()
            
            # 构建对话上下文
            context = await self._build_context(enhanced_data)
            
            # 初始化流式存储
            stream_key = f"stream:{uid}:{session_id}"
            await self._init_stream_storage(redis_client, stream_key, enhanced_data)
            
            # 更新状态为流式输出
            status_info.status = ChatStatus.STREAMING
            status_info.message = "开始流式生成回复"
            status_info.progress = 0.3
            
            # 流式生成对话
            response_content = ""
            tokens_used = 0
            
            async for chunk_data in self._generate_stream_response(context, enhanced_data):
                # 写入Redis流式存储
                await self._write_stream_chunk(redis_client, stream_key, chunk_data)
                
                # 处理OpenAI客户端返回的不同类型的chunk
                chunk_type = chunk_data.get("type", "")
                logger.debug(f"📦 处理chunk类型: {chunk_type}")
                
                if chunk_type == "start":
                    # 开始信号
                    logger.info("🎯 收到开始信号")
                elif chunk_type == "response.output_text.delta":
                    # OpenAI流式响应的文本内容增量
                    delta_content = chunk_data.get("delta", "")
                    if delta_content:
                        response_content += delta_content
                        logger.debug(f"📝 累积内容长度: {len(response_content)}")
                elif chunk_type == "response.output_text.done":
                    # OpenAI流式响应的文本完成
                    full_text = chunk_data.get("text", "")
                    if full_text and not response_content:
                        # 如果没有通过delta累积到内容，使用完整文本
                        response_content = full_text
                        logger.info(f"📄 使用完整文本，长度: {len(response_content)}")
                elif chunk_type == "response.completed":
                    # 完成信号，包含usage信息
                    logger.info("🎉 收到完成信号")
                elif chunk_type == "usage":
                    # Token使用统计
                    tokens_used = chunk_data.get("total_tokens", 0)
                    logger.info(f"📊 Token使用: {tokens_used}")
                elif chunk_type == "complete":
                    # 我们自定义的完成信号
                    logger.info("✅ 收到自定义完成信号")
                elif chunk_type == "error":
                    # 错误信号
                    error_msg = chunk_data.get("error", "未知错误")
                    logger.error(f"❌ 收到错误信号: {error_msg}")
                    break
            
            # 完成处理
            completion_data = {
                **enhanced_data,
                "response_content": response_content,
                "tokens_used": tokens_used,
                "session_id": session_id,
                "stream_key": stream_key,
                "processing_timestamp": datetime.now(),
                "status": create_status_info(
                    ChatStatus.COMPLETED,
                    message="AI对话生成完成",
                    progress=1.0
                )
            }
            
            # 标记流式存储完成
            await self._complete_stream_storage(redis_client, stream_key, completion_data)
            
            logger.info(f"✅ 客户对话处理完成: {uid}, tokens: {tokens_used}")
            
            return completion_data
            
        except Exception as e:
            logger.error(f"❌ 客户对话处理失败 {uid}: {str(e)}")
            
            # 创建错误响应
            error_data = {
                **enhanced_data,
                "response_content": f"很抱歉，处理您的请求时出现了问题: {str(e)}",
                "tokens_used": 0,
                "session_id": session_id,
                "processing_error": str(e),
                "processing_timestamp": datetime.now(),
                "status": create_status_info(
                    ChatStatus.ERROR,
                    message=f"对话生成失败: {str(e)}",
                    error_details=str(e)
                )
            }
            
            return error_data
    
    async def _build_context(self, enhanced_data: Dict[str, Any]) -> str:
        """构建对话上下文"""
        try:
            memory: CustomerMemory = enhanced_data.get("customer_memory") 
            message = enhanced_data.get("message")
            
            # 使用固定的默认系统提示词
            system_prompt = self._get_default_system_prompt()
            
            # 构建对话历史（从数据库获取，暂时使用现有逻辑）
            conversation_history = self._build_conversation_history(memory)
            
            # 组合完整上下文，只拼接真正的变量
            context_parts = [
                f"系统提示词:\n{system_prompt}",
                f"对话历史:\n{conversation_history}" if conversation_history else "",
                f"用户输入:\n{message}"
            ]
            
            context = "\n\n".join(part for part in context_parts if part)
            
            logger.debug(f"构建上下文完成，长度: {len(context)} 字符")
            return context
            
        except Exception as e:
            logger.warning(f"上下文构建失败，使用简单模式: {str(e)}")
            return f"用户消息: {enhanced_data.get('message', '')}"
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        # TODO: 后续会从数据库获取，目前使用固定的默认提示词
        return """你是一个专业的AI助手，能够为用户提供优质的服务和支持。请用中文回复，保持友好和专业的态度。"""
    
    def _build_conversation_history(self, memory: CustomerMemory) -> str:
        """构建对话历史"""
        # TODO: 后续会从数据库获取历史对话，目前使用现有逻辑
        if not memory or not memory.short_term:
            return ""
        
        history_parts = []
        
        # 添加长期记忆摘要（如果有）
        if memory.long_term_summary:
            history_parts.append(f"历史对话摘要: {memory.long_term_summary}")
        
        # 添加最近对话
        for conv in memory.short_term[-5:]:  # 只取最近5条
            history_parts.append(f"用户: {conv.customer_message}")
            history_parts.append(f"AI: {conv.agent_message}")
        
        return "\n".join(history_parts)
    
    async def _init_stream_storage(self, redis_client, stream_key: str, enhanced_data: Dict[str, Any]):
        """初始化流式存储"""
        try:
            init_data = {
                "uid": enhanced_data.get("uid"),
                "session_id": enhanced_data.get("session_id"),
                "start_time": datetime.now().isoformat(),
                "status": "streaming",
                "chunks": []
            }
            
            await redis_client.hset(stream_key, "metadata", json.dumps(init_data))
            await redis_client.expire(stream_key, self.settings.redis.stream_ttl)
            
        except Exception as e:
            logger.warning(f"流式存储初始化失败: {str(e)}")
    
    async def _write_stream_chunk(self, redis_client, stream_key: str, chunk_data: Dict[str, Any]):
        """写入流式数据块"""
        try:
            chunk_with_timestamp = {
                **chunk_data,
                "timestamp": datetime.now().isoformat()
            }
            
            await redis_client.lpush(
                f"{stream_key}:chunks", 
                json.dumps(chunk_with_timestamp, ensure_ascii=False)
            )
            
            # 限制chunks数量，避免内存过度使用
            await redis_client.ltrim(f"{stream_key}:chunks", 0, 1000)
            
        except Exception as e:
            logger.warning(f"流式数据写入失败: {str(e)}")
    
    async def _complete_stream_storage(self, redis_client, stream_key: str, completion_data: Dict[str, Any]):
        """完成流式存储"""
        try:
            completion_info = {
                "status": "completed",
                "end_time": datetime.now().isoformat(),
                "total_tokens": completion_data.get("tokens_used", 0),
                "response_length": len(completion_data.get("response_content", ""))
            }
            
            await redis_client.hset(stream_key, "completion", json.dumps(completion_info))
            
        except Exception as e:
            logger.warning(f"流式存储完成标记失败: {str(e)}")
    
    async def _generate_stream_response(self, context: str, enhanced_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """生成流式响应（调用OpenAI客户端）"""
        client = None
        try:
            # 使用服务配置（不允许请求覆盖）
            api_key = self.settings.openai.api_key
            base_url = self.settings.openai.base_url
            # mcp_url = "http://39.103.228.66:8165/mcp/"
            mcp_urls = []  # MCP服务地址，可以考虑加入配置
            
            logger.info(f"🔧 准备创建OpenAI客户端...")
            logger.info(f"  - 模型: {self.settings.openai.model}")
            logger.info(f"  - Base URL: {base_url}")
            logger.info(f"  - MCP URL: {mcp_urls}")
            logger.info(f"  - API Key前8位: {api_key[:8] if api_key else 'None'}")
            
            # 创建OpenAI客户端
            from client.openai_client import OpenAIClient
            
            client_kwargs = {}
            if base_url:
                client_kwargs["base_url"] = base_url
            
            # 创建并初始化客户端
            logger.info("🚀 创建OpenAI客户端实例...")
            client = OpenAIClient(
                api_key=api_key,
                model=self.settings.openai.model,
                mcp_urls=mcp_urls,
                **client_kwargs
            )
            
            # 手动初始化客户端（调用__aenter__）
            logger.info("🔌 初始化客户端连接...")
            await client.__aenter__()
            logger.info("✅ 客户端初始化完成")
            
            # 发送开始信号
            logger.info("🎯 开始流式对话生成...")
            yield {"type": "start", "message": "开始生成回复"}
            
            # 调用流式对话
            chunk_count = 0
            logger.info("📡 调用client.stream_chat...")
            async for chunk in client.stream_chat(context):
                chunk_count += 1
                logger.debug(f"📦 收到第{chunk_count}个chunk: {chunk.get('type', 'unknown')}")
                # 直接yield OpenAI客户端返回的chunk
                yield chunk
            
            logger.info(f"✨ 流式对话完成，共收到{chunk_count}个chunks")
            
            # 发送usage统计信息（从客户端获取）
            if hasattr(client, 'usage') and client.usage:
                logger.info(f"📊 Token使用统计: 输入={client.usage.input_tokens}, 输出={client.usage.output_tokens}")
                yield {
                    "type": "usage",
                    "input_tokens": client.usage.input_tokens,
                    "output_tokens": client.usage.output_tokens,
                    "total_tokens": client.usage.input_tokens + client.usage.output_tokens
                }
            
            # 发送完成信号
            logger.info("🎉 发送完成信号")
            yield {"type": "complete", "message": "回复生成完成"}
            
        except Exception as e:
            logger.error(f"❌ 流式生成失败: {str(e)}")
            logger.error(f"   错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"   错误堆栈: {traceback.format_exc()}")
            yield {"type": "error", "error": str(e)}
            
        finally:
            # 确保客户端被正确关闭
            if client:
                try:
                    logger.info("🔌 关闭客户端连接...")
                    await client.__aexit__(None, None, None)
                    logger.info("✅ 客户端关闭完成")
                except Exception as e:
                    logger.warning(f"⚠️ 客户端关闭失败: {str(e)}") 