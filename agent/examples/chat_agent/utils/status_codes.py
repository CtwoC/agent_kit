"""
状态码定义
用于跟踪客户对话处理的各个阶段状态
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

class ChatStatus(str, Enum):
    """客户对话处理状态枚举"""
    # 初始状态
    PENDING = "pending"                    # 请求等待处理
    
    # 处理阶段
    LOADING_PROFILE = "loading_profile"    # 加载客户Profile
    PROCESSING = "processing"              # AI正在生成
    STREAMING = "streaming"                # 流式输出中
    STORING_PROFILE = "storing_profile"    # 更新客户记忆
    
    # 完成状态
    COMPLETED = "completed"                # 全流程完成
    
    # 错误状态
    ERROR = "error"                        # 处理异常
    TIMEOUT = "timeout"                    # 处理超时
    CANCELLED = "cancelled"                # 客户取消
    
    # 特殊状态
    PAUSED = "paused"                      # 暂停处理
    RECOVERING = "recovering"              # 错误恢复中

class ErrorCode(str, Enum):
    """错误代码"""
    # 系统错误
    INTERNAL_ERROR = "internal_error"
    REDIS_ERROR = "redis_error"
    OPENAI_ERROR = "openai_error"
    
    # 客户错误
    INVALID_REQUEST = "invalid_request"
    USER_BLOCKED = "user_blocked"
    RATE_LIMITED = "rate_limited"
    
    # 资源错误
    MEMORY_FULL = "memory_full"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVICE_UNAVAILABLE = "service_unavailable"

@dataclass
class StatusInfo:
    """状态信息数据类"""
    status: ChatStatus
    timestamp: datetime
    message: str = ""
    error_code: ErrorCode = None
    error_details: str = ""
    progress: float = 0.0  # 0.0 - 1.0
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "progress": self.progress
        }
        
        if self.error_code:
            result["error_code"] = self.error_code.value
            result["error_details"] = self.error_details
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusInfo":
        """从字典创建实例"""
        return cls(
            status=ChatStatus(data["status"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message=data.get("message", ""),
            error_code=ErrorCode(data["error_code"]) if data.get("error_code") else None,
            error_details=data.get("error_details", ""),
            progress=data.get("progress", 0.0),
            metadata=data.get("metadata")
        )

class StatusManager:
    """状态管理器"""
    
    # 状态转换规则
    VALID_TRANSITIONS = {
        ChatStatus.PENDING: [ChatStatus.LOADING_PROFILE, ChatStatus.ERROR, ChatStatus.CANCELLED],
        ChatStatus.LOADING_PROFILE: [ChatStatus.PROCESSING, ChatStatus.ERROR, ChatStatus.CANCELLED],
        ChatStatus.PROCESSING: [ChatStatus.STREAMING, ChatStatus.ERROR, ChatStatus.CANCELLED, ChatStatus.PAUSED],
        ChatStatus.STREAMING: [ChatStatus.STORING_PROFILE, ChatStatus.ERROR, ChatStatus.CANCELLED],
        ChatStatus.STORING_PROFILE: [ChatStatus.COMPLETED, ChatStatus.ERROR],
        ChatStatus.PAUSED: [ChatStatus.PROCESSING, ChatStatus.CANCELLED, ChatStatus.ERROR],
        ChatStatus.ERROR: [ChatStatus.RECOVERING, ChatStatus.CANCELLED],
        ChatStatus.RECOVERING: [ChatStatus.PROCESSING, ChatStatus.ERROR, ChatStatus.CANCELLED],
        ChatStatus.TIMEOUT: [ChatStatus.RECOVERING, ChatStatus.CANCELLED],
        ChatStatus.COMPLETED: [],  # 终态
        ChatStatus.CANCELLED: []   # 终态
    }
    
    @classmethod
    def can_transition(cls, from_status: ChatStatus, to_status: ChatStatus) -> bool:
        """检查状态转换是否有效"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])
    
    @classmethod
    def is_terminal_status(cls, status: ChatStatus) -> bool:
        """检查是否为终态"""
        return status in [ChatStatus.COMPLETED, ChatStatus.CANCELLED]
    
    @classmethod
    def is_error_status(cls, status: ChatStatus) -> bool:
        """检查是否为错误状态"""
        return status in [ChatStatus.ERROR, ChatStatus.TIMEOUT]
    
    @classmethod
    def is_processing_status(cls, status: ChatStatus) -> bool:
        """检查是否为处理中状态"""
        return status in [
            ChatStatus.LOADING_PROFILE,
            ChatStatus.PROCESSING, 
            ChatStatus.STREAMING,
            ChatStatus.STORING_PROFILE
        ]

# 预定义的状态信息
DEFAULT_STATUS_MESSAGES = {
    ChatStatus.PENDING: "请求等待处理",
    ChatStatus.LOADING_PROFILE: "正在加载客户资料",
    ChatStatus.PROCESSING: "AI正在思考中",
    ChatStatus.STREAMING: "正在生成回复",
    ChatStatus.STORING_PROFILE: "正在保存对话记录",
    ChatStatus.COMPLETED: "对话完成",
    ChatStatus.ERROR: "处理出现错误",
    ChatStatus.TIMEOUT: "处理超时",
    ChatStatus.CANCELLED: "客户取消了请求",
    ChatStatus.PAUSED: "处理已暂停",
    ChatStatus.RECOVERING: "正在尝试恢复"
}

def create_status_info(
    status: ChatStatus,
    message: str = None,
    error_code: ErrorCode = None,
    error_details: str = "",
    progress: float = 0.0,
    **metadata
) -> StatusInfo:
    """创建状态信息的便捷函数"""
    return StatusInfo(
        status=status,
        timestamp=datetime.now(),
        message=message or DEFAULT_STATUS_MESSAGES.get(status, ""),
        error_code=error_code,
        error_details=error_details,
        progress=progress,
        metadata=metadata if metadata else None
    ) 