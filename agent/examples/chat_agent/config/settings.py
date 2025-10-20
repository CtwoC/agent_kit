"""
Chat Agent配置管理
包含Redis、OpenAI、记忆系统等所有配置选项
"""

import os
import sys
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from .redis_config import RedisConfig

def check_required_env_vars():
    """检查必需的环境变量并提供友好的错误提示"""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API密钥，用于调用OpenAI服务",
        # 可以在这里添加其他必需的环境变量
    }
    
    missing_vars = []
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing_vars.append(f"  - {var_name}: {description}")
    
    if missing_vars:
        print("❌ 环境变量检查失败！")
        print("\n缺少以下必需的环境变量：")
        for var_info in missing_vars:
            print(var_info)
        
        print("\n请按以下方式设置环境变量：")
        print("\n🔧 方式1：在命令行中设置")
        print("Windows PowerShell:")
        for var_name in required_vars.keys():
            if var_name not in os.environ:
                print(f"  $env:{var_name}=\"your_value_here\"")
        
        print("\nWindows CMD:")
        for var_name in required_vars.keys():
            if var_name not in os.environ:
                print(f"  set {var_name}=your_value_here")
        
        print("\nLinux/Mac:")
        for var_name in required_vars.keys():
            if var_name not in os.environ:
                print(f"  export {var_name}=\"your_value_here\"")
        
        print("\n🔧 方式2：创建 .env 文件")
        print("在项目根目录创建 .env 文件，内容如下：")
        for var_name in required_vars.keys():
            if var_name not in os.environ:
                print(f"  {var_name}=your_value_here")
        
        print("\n💡 提示：")
        print("  - 获取OpenAI API密钥：https://platform.openai.com/api-keys")
        print("  - 设置环境变量后请重新启动程序")
        
        sys.exit(1)

class RedisSettings(BaseSettings):
    """Redis配置"""
    host: str = Field(default_factory=lambda: RedisConfig.get_redis_config()["host"], description="Redis主机地址")
    port: int = Field(default_factory=lambda: RedisConfig.get_redis_config()["port"], description="Redis端口")
    password: Optional[str] = Field(default_factory=lambda: RedisConfig.get_redis_config()["password"], description="Redis密码")
    db: int = Field(default_factory=lambda: RedisConfig.get_redis_config()["db"], description="Redis数据库编号")
    url: Optional[str] = Field(default_factory=lambda: RedisConfig.get_redis_url(), description="Redis连接URL")
    
    # 连接池配置
    max_connections: int = Field(default_factory=lambda: RedisConfig.get_redis_config()["max_connections"], description="最大连接数")
    retry_on_timeout: bool = Field(default_factory=lambda: RedisConfig.get_redis_config()["retry_on_timeout"], description="超时重试")
    
    # TTL配置
    stream_ttl: int = Field(default_factory=lambda: RedisConfig.get_redis_config()["stream_ttl"], description="流式数据TTL(秒)")
    profile_ttl: int = Field(default_factory=lambda: RedisConfig.get_redis_config()["profile_ttl"], description="Profile数据TTL(秒)")
    
    class Config:
        env_prefix = "REDIS_"

class OpenAISettings(BaseSettings):
    """OpenAI配置"""
    api_key: str = Field(description="OpenAI API密钥")
    base_url: Optional[str] = Field(default="http://43.130.31.174:8003/v1", description="API基础URL")
    model: str = Field(default="gpt-3.5-turbo", description="默认模型")
    max_tokens: int = Field(default=2000, description="最大token数")
    temperature: float = Field(default=0.7, description="创造性参数")
    timeout: int = Field(default=60, description="请求超时时间")
    
    class Config:
        env_prefix = "OPENAI_"

class MemorySettings(BaseSettings):
    """客户记忆系统配置"""
    max_history_length: int = Field(default=20, description="最大对话历史长度")
    context_window_size: int = Field(default=4000, description="上下文窗口大小(tokens)")
    compression_threshold: float = Field(default=0.8, description="压缩阈值")
    enable_personalization: bool = Field(default=True, description="启用个性化")
    enable_learning: bool = Field(default=True, description="启用学习功能")
    
    # 记忆类型权重
    short_term_weight: float = Field(default=1.0, description="短期记忆权重")
    long_term_weight: float = Field(default=0.5, description="长期记忆权重")
    preference_weight: float = Field(default=0.3, description="偏好权重")
    
    class Config:
        env_prefix = "MEMORY_"

class ConcurrencySettings(BaseSettings):
    """并发控制配置"""
    max_concurrent_users: int = Field(default=100, description="最大并发客户数")
    max_requests_per_user: int = Field(default=1, description="每客户最大请求数")
    request_timeout: int = Field(default=300, description="请求超时时间")
    cleanup_interval: int = Field(default=60, description="清理间隔(秒)")
    
    class Config:
        env_prefix = "CONCURRENCY_"

class StreamSettings(BaseSettings):
    """流式处理配置"""
    chunk_size: int = Field(default=50, description="chunk缓存大小")
    write_interval: float = Field(default=0.1, description="Redis写入间隔(秒)")
    read_interval: float = Field(default=0.05, description="Redis读取间隔(秒)")
    enable_compression: bool = Field(default=False, description="启用内容压缩")
    
    class Config:
        env_prefix = "STREAM_"

class MonitoringSettings(BaseSettings):
    """监控配置"""
    enable_metrics: bool = Field(default=True, description="启用指标收集")
    metrics_port: int = Field(default=9090, description="指标端口")
    log_level: str = Field(default="INFO", description="日志级别")
    enable_health_check: bool = Field(default=True, description="启用健康检查")
    
    class Config:
        env_prefix = "MONITORING_"

class AppSettings(BaseSettings):
    """应用主配置"""
    app_name: str = Field(default="Chat Agent", description="应用名称")
    version: str = Field(default="1.0.0", description="版本号")
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="服务主机")
    port: int = Field(default=8083, description="服务端口")
    
    # 子配置
    redis: RedisSettings = Field(default_factory=RedisSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    concurrency: ConcurrencySettings = Field(default_factory=ConcurrencySettings)
    stream: StreamSettings = Field(default_factory=StreamSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def create_settings() -> AppSettings:
    """创建配置实例，包含环境变量检查"""
    try:
        # 先检查必需的环境变量
        check_required_env_vars()
        
        # 创建配置实例
        return AppSettings()
    except Exception as e:
        if "Field required" in str(e) and "api_key" in str(e):
            # 如果是API密钥缺失错误，提供更友好的提示
            print("❌ 配置初始化失败！")
            print("\n请检查以下环境变量是否正确设置：")
            print("  - OPENAI_API_KEY: OpenAI API密钥")
            print("\n💡 获取API密钥：https://platform.openai.com/api-keys")
            sys.exit(1)
        else:
            # 其他配置错误
            print(f"❌ 配置初始化失败：{e}")
            sys.exit(1)

# 全局配置实例
settings = create_settings()

def get_settings() -> AppSettings:
    """获取配置实例"""
    return settings 