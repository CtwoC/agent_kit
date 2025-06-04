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
                
                # 累积内容
                if chunk_data.get("type") == "content":
                    response_content += chunk_data.get("chunk", "")
                    
                # 更新进度
                if chunk_data.get("type") == "progress":
                    status_info.progress = min(0.9, 0.3 + chunk_data.get("progress", 0) * 0.6)
                
                # 记录token使用情况
                if chunk_data.get("type") == "usage":
                    tokens_used = chunk_data.get("total_tokens", 0)
            
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
            profile: CustomerProfile = enhanced_data.get("customer_profile")
            memory: CustomerMemory = enhanced_data.get("customer_memory") 
            preferences = enhanced_data.get("customer_preferences", {})
            message = enhanced_data.get("message")
            
            # 构建系统提示词
            system_prompt = self._build_system_prompt(profile, preferences)
            
            # 构建对话历史
            conversation_history = self._build_conversation_history(memory)
            
            # 组合完整上下文
            context_parts = [
                f"系统提示词:\n{system_prompt}",
                f"对话历史:\n{conversation_history}" if conversation_history else "",
                f"客户当前消息:\n{message}"
            ]
            
            context = "\n\n".join(part for part in context_parts if part)
            
            logger.debug(f"构建上下文完成，长度: {len(context)} 字符")
            return context
            
        except Exception as e:
            logger.warning(f"上下文构建失败，使用简单模式: {str(e)}")
            return f"用户消息: {enhanced_data.get('message', '')}"
    
    def _build_system_prompt(self, profile: CustomerProfile, preferences: Dict[str, Any]) -> str:
        """构建个性化系统提示词"""
        base_prompt = """你是一个专业的AI客服助手，能够为客户提供优质的服务和支持。"""
        
        # 根据客户等级调整
        if profile.service_level == "premium":
            base_prompt += "\n你正在为VIP客户提供服务，请格外用心和专业。"
        elif profile.service_level == "enterprise":
            base_prompt += "\n你正在为企业客户提供服务，请保持商务专业的沟通风格。"
        
        # 根据历史满意度调整
        if profile.satisfaction_score and profile.satisfaction_score < 3.0:
            base_prompt += "\n这位客户之前的满意度较低，请特别耐心和细致地解答问题。"
        
        # 根据偏好调整
        if preferences.get("communication_style") == "formal":
            base_prompt += "\n请使用正式的沟通风格。"
        elif preferences.get("communication_style") == "casual":
            base_prompt += "\n请使用轻松友好的沟通风格。"
        
        if preferences.get("language") == "en":
            base_prompt += "\nPlease respond in English."
        else:
            base_prompt += "\n请用中文回复。"
        
        return base_prompt
    
    def _build_conversation_history(self, memory: CustomerMemory) -> str:
        """构建对话历史"""
        if not memory.short_term:
            return ""
        
        history_parts = []
        
        # 添加长期记忆摘要
        if memory.long_term_summary:
            history_parts.append(f"历史对话摘要: {memory.long_term_summary}")
        
        # 添加最近对话
        for conv in memory.short_term[-5:]:  # 只取最近5条
            history_parts.append(f"客户: {conv.customer_message}")
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
        """生成流式响应（模拟AI生成过程）"""
        try:
            # 模拟AI响应生成
            # 在实际实现中，这里会调用OpenAI客户端
            
            # 发送开始信号
            yield {"type": "start", "message": "开始生成回复"}
            
            # 模拟流式生成文本
            response_text = f"您好！我已经收到您的消息：{enhanced_data.get('message', '')}。作为您的AI助手，我很乐意为您提供帮助。"
            
            # 分chunk发送
            chunk_size = self.settings.stream.chunk_size
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                
                yield {
                    "type": "content",
                    "chunk": chunk,
                    "index": i // chunk_size
                }
                
                # 模拟生成延迟
                await asyncio.sleep(self.settings.stream.write_interval)
                
                # 发送进度更新
                progress = min(1.0, (i + chunk_size) / len(response_text))
                yield {"type": "progress", "progress": progress}
            
            # 发送使用情况统计
            yield {
                "type": "usage",
                "input_tokens": len(context) // 4,  # 粗略估算
                "output_tokens": len(response_text) // 4,
                "total_tokens": (len(context) + len(response_text)) // 4
            }
            
            # 发送完成信号
            yield {"type": "complete", "message": "回复生成完成"}
            
        except Exception as e:
            logger.error(f"流式生成失败: {str(e)}")
            yield {"type": "error", "error": str(e)} 