"""
客户对话API数据模型
定义所有客户对话接口的输入输出格式
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from utils.status_codes import ChatStatus, ErrorCode

class ChatRequest(BaseModel):
    """客户对话请求模型"""
    message: str = Field(description="客户消息内容")
    uid: str = Field(description="客户唯一标识")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="额外上下文")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="客户偏好设置")
    
class ChatResponse(BaseModel):
    """客户对话响应模型"""
    response: str = Field(description="AI回复内容")
    status: ChatStatus = Field(description="处理状态")
    session_id: str = Field(description="会话ID")
    timestamp: datetime = Field(description="响应时间")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="响应元数据")
    
class StreamStatus(BaseModel):
    """流式对话状态模型"""
    status: ChatStatus = Field(description="当前状态")
    content: str = Field(default="", description="当前生成内容")
    progress: float = Field(default=0.0, description="生成进度(0-1)")
    timestamp: datetime = Field(description="状态时间")
    error_code: Optional[ErrorCode] = Field(default=None, description="错误代码")
    error_details: Optional[str] = Field(default=None, description="错误详情")
    
class CustomerProfile(BaseModel):
    """客户Profile信息"""
    uid: str = Field(description="客户ID")
    created_at: datetime = Field(description="创建时间")
    last_active: datetime = Field(description="最后活跃时间")
    total_conversations: int = Field(description="总对话数")
    total_tokens: int = Field(description="总Token使用量")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="客户偏好")
    learning_data: Dict[str, Any] = Field(default_factory=dict, description="学习数据")
    satisfaction_score: Optional[float] = Field(default=None, description="满意度评分")
    service_level: str = Field(default="standard", description="服务等级")
    
class ConversationInfo(BaseModel):
    """对话信息"""
    id: str = Field(description="对话ID")
    timestamp: datetime = Field(description="对话时间")
    customer_message: str = Field(description="客户消息")
    agent_message: str = Field(description="AI回复")
    tokens_used: int = Field(description="使用的Token数")
    context_summary: Optional[str] = Field(default=None, description="上下文摘要")
    satisfaction_rating: Optional[int] = Field(default=None, description="满意度评分(1-5)")
    
class CustomerMemory(BaseModel):
    """客户记忆信息"""
    short_term: List[ConversationInfo] = Field(description="短期记忆")
    long_term_summary: Optional[str] = Field(default=None, description="长期记忆摘要")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="偏好记忆")
    total_context_tokens: int = Field(description="总上下文Token数")
    key_topics: List[str] = Field(default_factory=list, description="关键话题")
    
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="服务状态")
    service: str = Field(description="服务名称")
    version: str = Field(description="版本号")
    timestamp: datetime = Field(description="检查时间")
    redis_connected: bool = Field(description="Redis连接状态")
    active_customers: int = Field(description="活跃客户数")
    processing_customers: List[str] = Field(description="处理中的客户")
    
class SystemStatus(BaseModel):
    """系统状态"""
    uptime: float = Field(description="运行时间(秒)")
    memory_usage: Dict[str, Any] = Field(description="内存使用情况")
    redis_info: Dict[str, Any] = Field(description="Redis状态信息")
    active_connections: int = Field(description="活跃连接数")
    processed_conversations: int = Field(description="已处理对话数")
    error_count: int = Field(description="错误计数")
    average_satisfaction: Optional[float] = Field(default=None, description="平均满意度")
    
class MetricsResponse(BaseModel):
    """性能指标响应"""
    timestamp: datetime = Field(description="指标时间")
    conversations_per_second: float = Field(description="每秒对话数")
    average_response_time: float = Field(description="平均响应时间")
    concurrent_customers: int = Field(description="并发客户数")
    redis_operations_per_second: float = Field(description="Redis每秒操作数")
    memory_usage_mb: float = Field(description="内存使用量(MB)")
    cpu_usage_percent: float = Field(description="CPU使用率")
    customer_satisfaction_rate: Optional[float] = Field(default=None, description="客户满意率")
    
class ErrorResponse(BaseModel):
    """错误响应"""
    error_code: ErrorCode = Field(description="错误代码")
    message: str = Field(description="错误消息")
    details: Optional[str] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(description="错误时间")
    request_id: Optional[str] = Field(default=None, description="请求ID")
    
class StopRequest(BaseModel):
    """停止请求"""
    uid: str = Field(description="客户ID")
    reason: Optional[str] = Field(default="customer_cancelled", description="停止原因")
    
class ResetRequest(BaseModel):
    """重置请求"""
    uid: str = Field(description="客户ID")
    reset_type: str = Field(default="memory", description="重置类型")
    confirm: bool = Field(default=False, description="确认重置")
    
class FeedbackRequest(BaseModel):
    """客户反馈请求"""
    uid: str = Field(description="客户ID")
    conversation_id: str = Field(description="对话ID")
    rating: int = Field(ge=1, le=5, description="评分(1-5)")
    comment: Optional[str] = Field(default=None, description="评论")
    
class BulkOperation(BaseModel):
    """批量操作"""
    operation: str = Field(description="操作类型")
    customer_ids: List[str] = Field(description="客户ID列表")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="操作参数")
    
class ServiceConfig(BaseModel):
    """服务配置更新"""
    section: str = Field(description="配置节")
    key: str = Field(description="配置键")
    value: Any = Field(description="配置值")
    apply_immediately: bool = Field(default=False, description="立即应用") 