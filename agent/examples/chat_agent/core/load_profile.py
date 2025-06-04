"""
客户Profile加载模块
负责从Redis存储中加载客户历史对话、偏好设置和上下文记忆
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from utils.logger import get_logger
from utils.status_codes import ChatStatus, create_status_info
from models.api_models import CustomerProfile, CustomerMemory, ConversationInfo
from storage.redis_client import get_redis_client
from config.settings import get_settings

logger = get_logger(__name__)

class LoadProfile:
    """客户Profile加载处理器"""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理客户Profile加载
        
        Args:
            request_data: 包含uid等请求信息的字典
            
        Returns:
            Dict[str, Any]: 包含Profile数据的增强请求字典
        """
        uid = request_data.get("uid")
        session_id = request_data.get("session_id") 
        
        logger.info(f"🔍 开始加载客户Profile: {uid}")
        
        # 更新状态
        status_info = create_status_info(
            ChatStatus.LOADING_PROFILE,
            message=f"正在加载客户 {uid} 的资料",
            progress=0.1
        )
        
        try:
            # 获取Redis客户端
            redis_client = await get_redis_client()
            
            # 并行加载各种数据
            profile_task = self._load_customer_profile(redis_client, uid)
            memory_task = self._load_customer_memory(redis_client, uid)
            preferences_task = self._load_customer_preferences(redis_client, uid)
            
            # 等待所有数据加载完成
            profile, memory, preferences = await asyncio.gather(
                profile_task, memory_task, preferences_task,
                return_exceptions=True
            )
            
            # 处理加载异常
            if isinstance(profile, Exception):
                logger.warning(f"Profile加载异常: {profile}")
                profile = self._create_default_profile(uid)
                
            if isinstance(memory, Exception):
                logger.warning(f"Memory加载异常: {memory}")
                memory = self._create_default_memory()
                
            if isinstance(preferences, Exception):
                logger.warning(f"Preferences加载异常: {preferences}")
                preferences = {}
            
            # 更新进度
            status_info.progress = 0.8
            
            # 构建增强的请求数据
            enhanced_data = {
                **request_data,
                "customer_profile": profile,
                "customer_memory": memory,
                "customer_preferences": preferences,
                "load_timestamp": datetime.now(),
                "status": status_info
            }
            
            # 记录加载成功
            await self._record_load_activity(redis_client, uid)
            
            logger.info(f"✅ 客户Profile加载完成: {uid}")
            status_info.progress = 1.0
            status_info.message = "客户资料加载完成"
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ 客户Profile加载失败 {uid}: {str(e)}")
            
            # 创建默认数据并记录错误
            enhanced_data = {
                **request_data,
                "customer_profile": self._create_default_profile(uid),
                "customer_memory": self._create_default_memory(),
                "customer_preferences": {},
                "load_timestamp": datetime.now(),
                "load_error": str(e),
                "status": create_status_info(
                    ChatStatus.ERROR,
                    message=f"Profile加载失败: {str(e)}",
                    error_details=str(e)
                )
            }
            
            return enhanced_data
    
    async def _load_customer_profile(self, redis_client, uid: str) -> CustomerProfile:
        """加载客户基础Profile"""
        try:
            profile_key = f"profile:{uid}"
            profile_data = await redis_client.hgetall(profile_key)
            
            if not profile_data:
                return self._create_default_profile(uid)
            
            # 解析数据
            return CustomerProfile(
                uid=uid,
                created_at=datetime.fromisoformat(profile_data.get("created_at", datetime.now().isoformat())),
                last_active=datetime.fromisoformat(profile_data.get("last_active", datetime.now().isoformat())),
                total_conversations=int(profile_data.get("total_conversations", 0)),
                total_tokens=int(profile_data.get("total_tokens", 0)),
                preferences=eval(profile_data.get("preferences", "{}")),
                learning_data=eval(profile_data.get("learning_data", "{}")),
                satisfaction_score=float(profile_data.get("satisfaction_score")) if profile_data.get("satisfaction_score") else None,
                service_level=profile_data.get("service_level", "standard")
            )
            
        except Exception as e:
            logger.warning(f"Profile解析失败，使用默认: {str(e)}")
            return self._create_default_profile(uid)
    
    async def _load_customer_memory(self, redis_client, uid: str) -> CustomerMemory:
        """加载客户对话记忆"""
        try:
            memory_key = f"memory:{uid}"
            
            # 获取短期记忆（最近的对话）
            conversation_keys = await redis_client.lrange(f"{memory_key}:conversations", 0, self.settings.memory.max_history_length - 1)
            
            conversations = []
            for conv_key in conversation_keys:
                conv_data = await redis_client.hgetall(conv_key)
                if conv_data:
                    conversation = ConversationInfo(
                        id=conv_data.get("id"),
                        timestamp=datetime.fromisoformat(conv_data.get("timestamp")),
                        customer_message=conv_data.get("customer_message", ""),
                        agent_message=conv_data.get("agent_message", ""),
                        tokens_used=int(conv_data.get("tokens_used", 0)),
                        context_summary=conv_data.get("context_summary"),
                        satisfaction_rating=int(conv_data.get("satisfaction_rating")) if conv_data.get("satisfaction_rating") else None
                    )
                    conversations.append(conversation)
            
            # 获取长期记忆摘要
            long_term_summary = await redis_client.get(f"{memory_key}:summary")
            
            # 获取偏好记忆
            preferences_data = await redis_client.hgetall(f"{memory_key}:preferences")
            preferences = {k: eval(v) if v else None for k, v in preferences_data.items()}
            
            # 计算总token数
            total_tokens = sum(conv.tokens_used for conv in conversations)
            
            # 获取关键话题
            key_topics = await redis_client.lrange(f"{memory_key}:topics", 0, -1)
            
            return CustomerMemory(
                short_term=conversations,
                long_term_summary=long_term_summary,
                preferences=preferences,
                total_context_tokens=total_tokens,
                key_topics=key_topics or []
            )
            
        except Exception as e:
            logger.warning(f"Memory加载失败，使用默认: {str(e)}")
            return self._create_default_memory()
    
    async def _load_customer_preferences(self, redis_client, uid: str) -> Dict[str, Any]:
        """加载客户偏好设置"""
        try:
            prefs_key = f"preferences:{uid}"
            prefs_data = await redis_client.hgetall(prefs_key)
            
            return {k: eval(v) if v else None for k, v in prefs_data.items()}
            
        except Exception as e:
            logger.warning(f"Preferences加载失败: {str(e)}")
            return {}
    
    async def _record_load_activity(self, redis_client, uid: str):
        """记录加载活动"""
        try:
            activity_key = f"activity:{uid}"
            await redis_client.hset(activity_key, "last_load", datetime.now().isoformat())
            await redis_client.hincrby(activity_key, "load_count", 1)
        except Exception as e:
            logger.warning(f"记录加载活动失败: {str(e)}")
    
    def _create_default_profile(self, uid: str) -> CustomerProfile:
        """创建默认客户Profile"""
        return CustomerProfile(
            uid=uid,
            created_at=datetime.now(),
            last_active=datetime.now(),
            total_conversations=0,
            total_tokens=0,
            preferences={},
            learning_data={},
            satisfaction_score=None,
            service_level="standard"
        )
    
    def _create_default_memory(self) -> CustomerMemory:
        """创建默认客户记忆"""
        return CustomerMemory(
            short_term=[],
            long_term_summary=None,
            preferences={},
            total_context_tokens=0,
            key_topics=[]
        ) 