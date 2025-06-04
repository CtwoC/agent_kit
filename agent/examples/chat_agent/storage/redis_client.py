"""
Redis客户端封装
提供异步Redis操作接口和连接管理
"""

import asyncio
import redis.asyncio as redis
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager

from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)

class RedisClient:
    """异步Redis客户端封装"""
    
    def __init__(self):
        self.settings = get_settings()
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            # 创建连接池
            if self.settings.redis.url:
                self._pool = redis.ConnectionPool.from_url(
                    self.settings.redis.url,
                    max_connections=self.settings.redis.max_connections,
                    retry_on_timeout=self.settings.redis.retry_on_timeout
                )
            else:
                self._pool = redis.ConnectionPool(
                    host=self.settings.redis.host,
                    port=self.settings.redis.port,
                    password=self.settings.redis.password,
                    db=self.settings.redis.db,
                    max_connections=self.settings.redis.max_connections,
                    retry_on_timeout=self.settings.redis.retry_on_timeout
                )
            
            # 创建客户端
            self._client = redis.Redis(connection_pool=self._pool, decode_responses=True)
            
            # 测试连接
            await self._client.ping()
            
            logger.info("✅ Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Redis连接初始化失败: {str(e)}")
            raise
    
    async def close(self):
        """关闭Redis连接"""
        try:
            if self._client:
                await self._client.close()
            if self._pool:
                await self._pool.disconnect()
            
            logger.info("🔌 Redis连接已关闭")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis连接关闭时出现警告: {str(e)}")
    
    @property
    def client(self) -> redis.Redis:
        """获取Redis客户端实例"""
        if not self._client:
            raise RuntimeError("Redis客户端未初始化，请先调用initialize()")
        return self._client
    
    # 基础操作封装
    async def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        return await self.client.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """设置字符串值"""
        return await self.client.set(key, value, ex=ex)
    
    async def delete(self, *keys: str) -> int:
        """删除键"""
        return await self.client.delete(*keys)
    
    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        return await self.client.exists(*keys)
    
    async def expire(self, key: str, time: int) -> bool:
        """设置键过期时间"""
        return await self.client.expire(key, time)
    
    async def ttl(self, key: str) -> int:
        """获取键的TTL"""
        return await self.client.ttl(key)
    
    # Hash操作
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取Hash字段值"""
        return await self.client.hget(name, key)
    
    async def hset(self, name: str, key: Optional[str] = None, value: Optional[str] = None, mapping: Optional[Dict] = None) -> int:
        """设置Hash字段"""
        return await self.client.hset(name, key, value, mapping)
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """获取Hash所有字段"""
        return await self.client.hgetall(name)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """删除Hash字段"""
        return await self.client.hdel(name, *keys)
    
    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        """Hash字段递增"""
        return await self.client.hincrby(name, key, amount)
    
    # List操作
    async def lpush(self, name: str, *values: str) -> int:
        """从左侧推入列表"""
        return await self.client.lpush(name, *values)
    
    async def rpush(self, name: str, *values: str) -> int:
        """从右侧推入列表"""
        return await self.client.rpush(name, *values)
    
    async def lpop(self, name: str) -> Optional[str]:
        """从左侧弹出列表元素"""
        return await self.client.lpop(name)
    
    async def rpop(self, name: str) -> Optional[str]:
        """从右侧弹出列表元素"""
        return await self.client.rpop(name)
    
    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """获取列表范围"""
        return await self.client.lrange(name, start, end)
    
    async def ltrim(self, name: str, start: int, end: int) -> bool:
        """修剪列表"""
        return await self.client.ltrim(name, start, end)
    
    async def llen(self, name: str) -> int:
        """获取列表长度"""
        return await self.client.llen(name)
    
    # Set操作
    async def sadd(self, name: str, *values: str) -> int:
        """添加到集合"""
        return await self.client.sadd(name, *values)
    
    async def srem(self, name: str, *values: str) -> int:
        """从集合删除"""
        return await self.client.srem(name, *values)
    
    async def smembers(self, name: str) -> set:
        """获取集合所有成员"""
        return await self.client.smembers(name)
    
    async def scard(self, name: str) -> int:
        """获取集合大小"""
        return await self.client.scard(name)
    
    # 高级操作
    async def keys(self, pattern: str = "*") -> List[str]:
        """查找匹配模式的键"""
        return await self.client.keys(pattern)
    
    async def ping(self) -> bool:
        """测试连接"""
        result = await self.client.ping()
        return result == True
    
    async def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """获取Redis信息"""
        return await self.client.info(section)
    
    async def flushdb(self) -> bool:
        """清空当前数据库"""
        return await self.client.flushdb()
    
    async def dbsize(self) -> int:
        """获取数据库键数量"""
        return await self.client.dbsize()


# 全局Redis客户端实例
_redis_client: Optional[RedisClient] = None

async def get_redis_client() -> RedisClient:
    """获取全局Redis客户端实例"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.initialize()
    
    return _redis_client

async def close_redis_client():
    """关闭全局Redis客户端"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

@asynccontextmanager
async def redis_context():
    """Redis上下文管理器"""
    client = await get_redis_client()
    try:
        yield client
    except Exception as e:
        logger.error(f"Redis操作异常: {str(e)}")
        raise
    finally:
        # 注意：这里不关闭连接，因为是全局共享的
        pass 