"""
Redis连接配置
包含生产环境的Redis连接信息
"""

import os
from typing import Optional

class RedisConfig:
    """Redis配置类"""
    
    # 生产环境Redis配置
    PROD_HOST = "r-uf6805sowwjiimkgospd.redis.rds.aliyuncs.com"
    PROD_PORT = 6379
    PROD_DB = 16
    PROD_PASSWORD = "video_app_prod:video_app@2023"
    
    # 默认配置
    DEFAULT_MAX_CONNECTIONS = 100
    DEFAULT_RETRY_ON_TIMEOUT = True
    DEFAULT_STREAM_TTL = 3600  # 1小时
    DEFAULT_PROFILE_TTL = 604800  # 7天
    
    @classmethod
    def get_redis_config(cls) -> dict:
        """获取Redis配置"""
        return {
            "host": os.getenv("REDIS_HOST", cls.PROD_HOST),
            "port": int(os.getenv("REDIS_PORT", cls.PROD_PORT)),
            "db": int(os.getenv("REDIS_DB", cls.PROD_DB)),
            "password": os.getenv("REDIS_PASSWORD", cls.PROD_PASSWORD),
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", cls.DEFAULT_MAX_CONNECTIONS)),
            "retry_on_timeout": os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true",
            "stream_ttl": int(os.getenv("REDIS_STREAM_TTL", cls.DEFAULT_STREAM_TTL)),
            "profile_ttl": int(os.getenv("REDIS_PROFILE_TTL", cls.DEFAULT_PROFILE_TTL))
        }
    
    @classmethod
    def get_redis_url(cls) -> str:
        """获取Redis连接URL"""
        config = cls.get_redis_config()
        if config["password"]:
            return f"redis://:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
        else:
            return f"redis://{config['host']}:{config['port']}/{config['db']}" 