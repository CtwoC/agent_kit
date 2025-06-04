"""
客户Profile存储模块
负责将对话结果存储到Redis，更新客户记忆和历史记录
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta

from utils.logger import get_logger
from utils.status_codes import ChatStatus, create_status_info
from models.api_models import CustomerProfile, CustomerMemory, ConversationInfo
from storage.redis_client import get_redis_client
from config.settings import get_settings

logger = get_logger(__name__)

class StoreProfile:
    """客户Profile存储处理器"""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def process(self, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理客户Profile存储
        
        Args:
            completion_data: 包含对话处理结果的字典
            
        Returns:
            Dict[str, Any]: 包含存储结果的字典
        """
        uid = completion_data.get("uid")
        
        logger.info(f"💾 开始存储客户Profile: {uid}")
        
        # 更新状态
        status_info = create_status_info(
            ChatStatus.STORING_PROFILE,
            message=f"正在保存客户 {uid} 的对话记录",
            progress=0.9
        )
        
        try:
            # 获取Redis客户端
            redis_client = await get_redis_client()
            
            # 并行执行各种存储任务
            tasks = [
                self._store_conversation_history(redis_client, completion_data),
                self._update_customer_profile(redis_client, completion_data),
                self._update_customer_memory(redis_client, completion_data),
                self._update_customer_preferences(redis_client, completion_data),
                self._record_usage_statistics(redis_client, completion_data)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查存储结果
            storage_errors = [r for r in results if isinstance(r, Exception)]
            if storage_errors:
                logger.warning(f"部分存储操作失败: {[str(e) for e in storage_errors]}")
            
            # 清理旧数据
            await self._cleanup_old_data(redis_client, uid)
            
            # 构建最终结果
            final_result = {
                **completion_data,
                "storage_timestamp": datetime.now(),
                "storage_errors": [str(e) for e in storage_errors] if storage_errors else None,
                "status": create_status_info(
                    ChatStatus.COMPLETED,
                    message="客户资料保存完成",
                    progress=1.0
                )
            }
            
            logger.info(f"✅ 客户Profile存储完成: {uid}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ 客户Profile存储失败 {uid}: {str(e)}")
            
            # 创建错误结果
            error_result = {
                **completion_data,
                "storage_timestamp": datetime.now(),
                "storage_error": str(e),
                "status": create_status_info(
                    ChatStatus.ERROR,
                    message=f"Profile存储失败: {str(e)}",
                    error_details=str(e)
                )
            }
            
            return error_result
    
    async def _store_conversation_history(self, redis_client, completion_data: Dict[str, Any]):
        """存储对话历史"""
        try:
            uid = completion_data.get("uid")
            session_id = completion_data.get("session_id")
            
            # 创建对话记录
            conversation = ConversationInfo(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                customer_message=completion_data.get("message", ""),
                agent_message=completion_data.get("response_content", ""),
                tokens_used=completion_data.get("tokens_used", 0),
                context_summary=self._generate_context_summary(completion_data),
                satisfaction_rating=None  # 等待客户反馈
            )
            
            # 存储到Redis
            conv_key = f"conversation:{uid}:{conversation.id}"
            conv_data = {
                "id": conversation.id,
                "timestamp": conversation.timestamp.isoformat(),
                "customer_message": conversation.customer_message,
                "agent_message": conversation.agent_message,
                "tokens_used": str(conversation.tokens_used),
                "context_summary": conversation.context_summary or "",
                "session_id": session_id or ""
            }
            
            await redis_client.hset(conv_key, mapping=conv_data)
            await redis_client.expire(conv_key, self.settings.redis.profile_ttl)
            
            # 添加到用户对话列表
            memory_key = f"memory:{uid}"
            await redis_client.lpush(f"{memory_key}:conversations", conv_key)
            
            # 限制对话历史长度
            await redis_client.ltrim(
                f"{memory_key}:conversations", 
                0, 
                self.settings.memory.max_history_length - 1
            )
            
            logger.debug(f"对话历史存储成功: {uid}")
            
        except Exception as e:
            logger.error(f"对话历史存储失败: {str(e)}")
            raise
    
    async def _update_customer_profile(self, redis_client, completion_data: Dict[str, Any]):
        """更新客户基础Profile"""
        try:
            uid = completion_data.get("uid")
            profile: CustomerProfile = completion_data.get("customer_profile")
            
            if not profile:
                return
            
            # 更新统计数据
            profile.last_active = datetime.now()
            profile.total_conversations += 1
            profile.total_tokens += completion_data.get("tokens_used", 0)
            
            # 存储更新后的Profile
            profile_key = f"profile:{uid}"
            profile_data = {
                "uid": profile.uid,
                "created_at": profile.created_at.isoformat(),
                "last_active": profile.last_active.isoformat(),
                "total_conversations": str(profile.total_conversations),
                "total_tokens": str(profile.total_tokens),
                "preferences": json.dumps(profile.preferences),
                "learning_data": json.dumps(profile.learning_data),
                "satisfaction_score": str(profile.satisfaction_score) if profile.satisfaction_score else "",
                "service_level": profile.service_level
            }
            
            await redis_client.hset(profile_key, mapping=profile_data)
            await redis_client.expire(profile_key, self.settings.redis.profile_ttl)
            
            logger.debug(f"客户Profile更新成功: {uid}")
            
        except Exception as e:
            logger.error(f"客户Profile更新失败: {str(e)}")
            raise
    
    async def _update_customer_memory(self, redis_client, completion_data: Dict[str, Any]):
        """更新客户记忆系统"""
        try:
            uid = completion_data.get("uid")
            memory: CustomerMemory = completion_data.get("customer_memory")
            
            if not memory:
                return
            
            memory_key = f"memory:{uid}"
            
            # 更新关键话题
            new_topics = self._extract_topics(completion_data)
            if new_topics:
                for topic in new_topics:
                    await redis_client.lpush(f"{memory_key}:topics", topic)
                
                # 限制话题数量
                await redis_client.ltrim(f"{memory_key}:topics", 0, 50)
            
            # 更新长期记忆摘要（如果对话数量达到阈值）
            if len(memory.short_term) >= 10:  # 每10次对话更新一次摘要
                summary = await self._generate_long_term_summary(memory.short_term)
                await redis_client.set(f"{memory_key}:summary", summary)
                await redis_client.expire(f"{memory_key}:summary", self.settings.redis.profile_ttl)
            
            logger.debug(f"客户记忆更新成功: {uid}")
            
        except Exception as e:
            logger.error(f"客户记忆更新失败: {str(e)}")
            raise
    
    async def _update_customer_preferences(self, redis_client, completion_data: Dict[str, Any]):
        """更新客户偏好设置"""
        try:
            uid = completion_data.get("uid")
            
            # 学习客户偏好（简单示例）
            learned_preferences = self._learn_preferences(completion_data)
            
            if learned_preferences:
                prefs_key = f"preferences:{uid}"
                prefs_data = {k: json.dumps(v) for k, v in learned_preferences.items()}
                
                await redis_client.hset(prefs_key, mapping=prefs_data)
                await redis_client.expire(prefs_key, self.settings.redis.profile_ttl)
            
            logger.debug(f"客户偏好更新成功: {uid}")
            
        except Exception as e:
            logger.error(f"客户偏好更新失败: {str(e)}")
            raise
    
    async def _record_usage_statistics(self, redis_client, completion_data: Dict[str, Any]):
        """记录使用统计"""
        try:
            uid = completion_data.get("uid")
            tokens_used = completion_data.get("tokens_used", 0)
            
            # 记录每日统计
            today = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"stats:daily:{today}"
            
            await redis_client.hincrby(daily_key, "total_conversations", 1)
            await redis_client.hincrby(daily_key, "total_tokens", tokens_used)
            await redis_client.sadd(f"{daily_key}:users", uid)
            await redis_client.expire(daily_key, 86400 * 30)  # 保留30天
            
            # 记录用户统计
            user_stats_key = f"stats:user:{uid}"
            await redis_client.hincrby(user_stats_key, "conversations_today", 1)
            await redis_client.hincrby(user_stats_key, "tokens_today", tokens_used)
            await redis_client.expire(user_stats_key, 86400)  # 每日重置
            
            logger.debug(f"使用统计记录成功: {uid}")
            
        except Exception as e:
            logger.error(f"使用统计记录失败: {str(e)}")
            raise
    
    async def _cleanup_old_data(self, redis_client, uid: str):
        """清理过期数据"""
        try:
            # 清理过期的流式数据
            pattern = f"stream:{uid}:*"
            keys = await redis_client.keys(pattern)
            
            for key in keys:
                # 检查是否过期
                ttl = await redis_client.ttl(key)
                if ttl < 60:  # 小于1分钟就清理
                    await redis_client.delete(key)
            
            logger.debug(f"数据清理完成: {uid}")
            
        except Exception as e:
            logger.warning(f"数据清理失败: {str(e)}")
    
    def _generate_context_summary(self, completion_data: Dict[str, Any]) -> str:
        """生成对话上下文摘要"""
        try:
            message = completion_data.get("message", "")
            response = completion_data.get("response_content", "")
            
            # 简单的摘要生成（实际可以使用更复杂的算法）
            if len(message) > 100:
                message_summary = message[:50] + "..."
            else:
                message_summary = message
            
            return f"客户询问: {message_summary}"
            
        except Exception as e:
            logger.warning(f"上下文摘要生成失败: {str(e)}")
            return "对话摘要生成失败"
    
    def _extract_topics(self, completion_data: Dict[str, Any]) -> List[str]:
        """提取对话主题"""
        try:
            message = completion_data.get("message", "").lower()
            
            # 简单的主题提取（实际可以使用NLP技术）
            topic_keywords = {
                "技术支持": ["问题", "错误", "故障", "帮助", "支持"],
                "产品咨询": ["产品", "功能", "特性", "价格", "购买"],
                "投诉建议": ["不满", "投诉", "建议", "改进", "问题"],
                "账户服务": ["账户", "登录", "密码", "设置", "个人"]
            }
            
            topics = []
            for topic, keywords in topic_keywords.items():
                if any(keyword in message for keyword in keywords):
                    topics.append(topic)
            
            return topics if topics else ["一般咨询"]
            
        except Exception as e:
            logger.warning(f"主题提取失败: {str(e)}")
            return []
    
    async def _generate_long_term_summary(self, conversations: List[ConversationInfo]) -> str:
        """生成长期记忆摘要"""
        try:
            if not conversations:
                return ""
            
            # 简单的摘要生成（实际可以使用AI生成摘要）
            recent_topics = []
            for conv in conversations[-5:]:  # 最近5次对话
                if conv.context_summary:
                    recent_topics.append(conv.context_summary)
            
            summary = f"最近关注话题: {', '.join(recent_topics)}" if recent_topics else "暂无特定话题"
            
            return summary
            
        except Exception as e:
            logger.warning(f"长期记忆摘要生成失败: {str(e)}")
            return "摘要生成失败"
    
    def _learn_preferences(self, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """学习客户偏好"""
        try:
            preferences = {}
            
            message = completion_data.get("message", "")
            
            # 检测语言偏好
            if any(ord(char) > 127 for char in message):
                preferences["language"] = "zh"
            else:
                preferences["language"] = "en"
            
            # 检测沟通风格（简单示例）
            formal_indicators = ["您好", "请问", "谢谢", "麻烦"]
            casual_indicators = ["你好", "咋样", "啥", "哈哈"]
            
            formal_count = sum(1 for indicator in formal_indicators if indicator in message)
            casual_count = sum(1 for indicator in casual_indicators if indicator in message)
            
            if formal_count > casual_count:
                preferences["communication_style"] = "formal"
            elif casual_count > formal_count:
                preferences["communication_style"] = "casual"
            
            return preferences
            
        except Exception as e:
            logger.warning(f"偏好学习失败: {str(e)}")
            return {} 