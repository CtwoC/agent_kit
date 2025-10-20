#!/usr/bin/env python3
"""
Chat Agent主应用
基于Redis流式中转和智能记忆系统的客户对话服务
"""

import asyncio
import uuid
import json
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime
import time
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 导入核心模块
from core import CoreFlow, process_chat_request
from config import get_settings
from utils.logger import get_logger
from utils.status_codes import ChatStatus, ErrorCode
from models.api_models import (
    ChatRequest, ChatResponse, HealthResponse, 
    SystemStatus, MetricsResponse, ErrorResponse
)
from storage.redis_client import get_redis_client, close_redis_client

# 用户并发控制
from typing import Set
user_processing: Set[str] = set()
user_lock = asyncio.Lock()

logger = get_logger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动Chat Agent服务...")
    
    # 初始化Redis连接
    try:
        redis_client = await get_redis_client()
        logger.info("✅ Redis连接初始化成功")
    except Exception as e:
        logger.error(f"❌ Redis连接失败: {str(e)}")
        raise
    
    # 启动完成
    logger.info(f"🌟 Chat Agent服务启动完成 - {settings.app_name} v{settings.version}")
    logger.info(f"🔗 服务地址: http://{settings.host}:{settings.port}")
    
    yield
    
    # 关闭时清理
    logger.info("🔄 正在关闭Chat Agent服务...")
    await close_redis_client()
    logger.info("✅ 服务已安全关闭")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="基于Redis流式中转和智能记忆系统的客户对话服务",
    lifespan=lifespan
)

# 用户并发控制函数
async def check_and_mark_user_processing(uid: str) -> bool:
    """检查并标记用户处理状态"""
    async with user_lock:
        if uid in user_processing:
            return False
        user_processing.add(uid)
        logger.info(f"🔒 用户 {uid} 开始处理")
        return True

async def unmark_user_processing(uid: str):
    """取消用户处理标记"""
    async with user_lock:
        user_processing.discard(uid)
        logger.info(f"🔓 用户 {uid} 处理完成")

# API端点定义

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "features": [
            "智能客户对话",
            "Redis流式中转", 
            "客户记忆系统",
            "用户级并发控制",
            "个性化服务"
        ],
        "endpoints": [
            "/chat",
            "/chat/stream", 
            "/health",
            "/status",
            "/metrics"
        ],
        "documentation": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """快速健康检查 - 不执行慢速操作"""
    try:
        # 获取处理状态（快速操作）
        async with user_lock:
            active_customers = len(user_processing)
            processing_customers = list(user_processing)
        
        # 快速Redis检查 - 只检查连接是否存在
        redis_connected = True
        try:
            redis_client = await get_redis_client()
            redis_connected = redis_client._client is not None
        except Exception:
            redis_connected = False
        
        return HealthResponse(
            status="healthy",
            service=settings.app_name,
            version=settings.version,
            timestamp=datetime.now(),
            redis_connected=redis_connected,
            active_customers=active_customers,
            processing_customers=processing_customers
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@app.get("/health/deep")
async def deep_health_check():
    """深度健康检查 - 包含Redis ping等慢速操作"""
    try:
        # 获取处理状态
        async with user_lock:
            active_customers = len(user_processing)
            processing_customers = list(user_processing)
        
        # 深度Redis检查 - 执行ping操作
        redis_connected = False
        redis_ping_time = 0.0
        try:
            start_time = time.time()
            redis_client = await get_redis_client()
            redis_connected = await redis_client.ping()
            redis_ping_time = time.time() - start_time
        except Exception as e:
            logger.warning(f"Redis ping失败: {str(e)}")
        
        return {
            "status": "healthy" if redis_connected else "degraded",
            "service": settings.app_name,
            "version": settings.version,
            "timestamp": datetime.now().isoformat(),
            "redis_connected": redis_connected,
            "redis_ping_time": f"{redis_ping_time:.3f}s",
            "active_customers": active_customers,
            "processing_customers": processing_customers,
            "check_type": "deep"
        }
        
    except Exception as e:
        logger.error(f"深度健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"深度健康检查失败: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_non_stream(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    非流式聊天端点
    完整的三步流程：Load Profile -> Chat Processor -> Store Profile
    """
    uid = request.uid
    
    # 检查用户是否已在处理中
    can_process = await check_and_mark_user_processing(uid)
    if not can_process:
        raise HTTPException(
            status_code=429,
            detail=f"用户 {uid} 有请求正在处理中，请等待完成后再试"
        )
    
    try:
        logger.info(f"💬 开始处理非流式聊天: {uid}")
        
        # 构建请求数据
        request_data = {
            "uid": uid,
            "message": request.message,
            "session_id": request.session_id or str(uuid.uuid4()),
            "context": request.context or {},
            "preferences": request.preferences or {}
        }
        
        # 执行核心流程
        result = await process_chat_request(request_data, parallel=False)
        
        # 构建响应
        if result.get("flow_completed"):
            response = ChatResponse(
                response=result.get("response_content", ""),
                status=ChatStatus.COMPLETED,
                session_id=result.get("session_id"),
                timestamp=datetime.now(),
                metadata={
                    "tokens_used": result.get("tokens_used", 0),
                    "flow_duration": result.get("flow_duration", 0),
                    "processing_timestamp": result.get("processing_timestamp")
                }
            )
            
            logger.info(f"✅ 非流式聊天完成: {uid}")
            return response
        else:
            # 处理失败
            error_msg = result.get("flow_error", "未知错误")
            logger.error(f"❌ 非流式聊天失败: {uid} - {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 非流式聊天异常: {uid} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理聊天请求时发生错误: {str(e)}")
    
    finally:
        # 确保释放用户处理标记
        background_tasks.add_task(unmark_user_processing, uid)

@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """
    流式聊天端点
    返回Server-Sent Events格式的流式响应
    """
    uid = request.uid
    
    # 检查用户是否已在处理中
    can_process = await check_and_mark_user_processing(uid)
    if not can_process:
        error_msg = f"用户 {uid} 有请求正在处理中，请等待完成后再试"
        logger.warning(f"⚠️ {error_msg}")
        
        # 返回错误的流式响应
        async def error_response():
            error_data = {
                'type': 'error', 
                'error': error_msg, 
                'uid': uid,
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            error_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    # 流式处理
    async def stream_with_cleanup():
        """带清理的流式响应生成器"""
        processing_task = None
        try:
            logger.info(f"🌊 开始流式聊天处理: {uid}")
            
            # 构建请求数据
            request_data = {
                "uid": uid,
                "message": request.message,
                "session_id": request.session_id or str(uuid.uuid4()),
                "context": request.context or {},
                "preferences": request.preferences or {}
            }
            
            # 发送开始事件
            start_event = {
                "type": "start",
                "message": "开始处理客户请求",
                "uid": uid,
                "session_id": request_data["session_id"],
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(start_event, ensure_ascii=False)}\n\n"
            
            # 启动处理任务（异步执行）
            processing_task = asyncio.create_task(
                process_chat_request(request_data, parallel=False)
            )
            
            # 获取Redis客户端
            redis_client = await get_redis_client()
            
            # 实时读取chunks
            chunks_sent = 0
            processing_completed = False
            
            # 使用与ChatProcessor相同的stream_key格式
            expected_stream_key = f"stream:{uid}:{request_data['session_id']}"
            
            while not processing_completed:
                try:
                    # 检查处理任务是否完成
                    if processing_task.done():
                        processing_completed = True
                        result = await processing_task
                        
                        # 确认最终的stream_key
                        if result.get("stream_key"):
                            expected_stream_key = result["stream_key"]
                    
                    # 读取新的chunks
                    chunks = await redis_client.lrange(f"{expected_stream_key}:chunks", 0, -1)
                    
                    if chunks:
                        # 发送新的chunks（从上次发送的位置开始）
                        total_chunks = len(chunks)
                        if total_chunks > chunks_sent:
                            # 由于使用lpush，新的chunks在前面，需要反转并选择新的
                            new_chunks = list(reversed(chunks))[chunks_sent:]
                            
                            for chunk_json in new_chunks:
                                try:
                                    chunk_data = json.loads(chunk_json)
                                    chunk_type = chunk_data.get("type", "")
                                    
                                    # 发送所有有意义的chunks，不只是delta
                                    if chunk_type in ["response.output_text.delta", "response.output_text.done", "usage", "response.completed"]:
                                        # 添加调试日志
                                        logger.info(f"🌊 发送chunk类型: {chunk_type}")
                                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                                except json.JSONDecodeError:
                                    continue
                            
                            chunks_sent = total_chunks
                    
                    # 如果处理未完成，等待一小段时间再检查
                    if not processing_completed:
                        await asyncio.sleep(0.1)  # 100ms检查间隔
                        
                except Exception as e:
                    logger.error(f"读取chunks时出错: {str(e)}")
                    await asyncio.sleep(0.1)
            
            # 处理完成后，确保所有chunks都已发送
            if processing_task.done():
                result = await processing_task
                
                # 发送完成事件
                completion_event = {
                    "type": "complete",
                    "message": "处理完成",
                    "uid": uid,
                    "session_id": request_data["session_id"],
                    "full_content": result.get("response_content", ""),
                    "metadata": {
                        "tokens_used": result.get("tokens_used", 0),
                        "flow_duration": result.get("flow_duration", 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(completion_event, ensure_ascii=False)}\n\n"
                
                logger.info(f"✅ 流式聊天完成: {uid}")
            
        except Exception as e:
            logger.error(f"❌ 流式聊天异常: {uid} - {str(e)}")
            
            # 取消处理任务
            if processing_task and not processing_task.done():
                processing_task.cancel()
                
            error_event = {
                "type": "error",
                "error": f"处理请求时发生错误: {str(e)}",
                "uid": uid,
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        
        finally:
            # 确保取消用户处理标记
            await unmark_user_processing(uid)
    
    return StreamingResponse(
        stream_with_cleanup(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    try:
        # 获取Redis信息
        redis_client = await get_redis_client()
        redis_info = await redis_client.info()
        
        # 获取用户状态
        async with user_lock:
            active_connections = len(user_processing)
        
        # 系统运行时间（简化版）
        uptime = 0.0  # 这里可以记录服务启动时间来计算真实uptime
        
        return SystemStatus(
            uptime=uptime,
            memory_usage={
                "redis_used_memory": redis_info.get("used_memory", 0),
                "redis_used_memory_human": redis_info.get("used_memory_human", "0B")
            },
            redis_info={
                "version": redis_info.get("redis_version", "unknown"),
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory": redis_info.get("used_memory", 0)
            },
            active_connections=active_connections,
            processed_conversations=0,  # 这里可以从Redis统计数据获取
            error_count=0,  # 这里可以维护错误计数器
            average_satisfaction=None
        )
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """获取性能指标"""
    try:
        # 获取当前用户状态
        async with user_lock:
            concurrent_customers = len(user_processing)
        
        # 获取Redis信息
        redis_client = await get_redis_client()
        redis_info = await redis_client.info()
        
        return MetricsResponse(
            timestamp=datetime.now(),
            conversations_per_second=0.0,  # 需要实现统计逻辑
            average_response_time=0.0,     # 需要实现统计逻辑
            concurrent_customers=concurrent_customers,
            redis_operations_per_second=0.0,  # 需要实现统计逻辑
            memory_usage_mb=redis_info.get("used_memory", 0) / 1024 / 1024,
            cpu_usage_percent=0.0,  # 需要系统资源监控
            customer_satisfaction_rate=None
        )
        
    except Exception as e:
        logger.error(f"获取性能指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")

@app.get("/stats")
async def get_stats():
    """获取处理统计信息"""
    async with user_lock:
        active_users = len(user_processing)
        processing_users = list(user_processing)
    
    return {
        "service_stats": {
            "active_users": active_users,
            "processing_users": processing_users,
            "timestamp": datetime.now().isoformat()
        }
    }

# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "内部服务器错误",
                "timestamp": datetime.now().isoformat()
            }
        }
    )

def main():
    """主函数"""
    print(f"🌊 启动 {settings.app_name} v{settings.version}")
    print("="*60)
    print("📖 Chat Agent特性:")
    print("   ✅ Redis流式中转 - 服务重启不丢失数据") 
    print("   ✅ 智能记忆系统 - 个性化客户服务")
    print("   ✅ 用户级并发控制 - 高性能处理")
    print("   ✅ 三步处理流程 - Load → Process → Store")
    print()
    print("🔗 API端点:")
    print(f"   💬 聊天接口: POST http://{settings.host}:{settings.port}/chat")
    print(f"   🌊 流式接口: POST http://{settings.host}:{settings.port}/chat/stream")
    print(f"   ❤️ 健康检查: GET http://{settings.host}:{settings.port}/health")
    print(f"   📊 系统状态: GET http://{settings.host}:{settings.port}/status")
    print(f"   📈 性能指标: GET http://{settings.host}:{settings.port}/metrics")
    print(f"   📚 API文档: http://{settings.host}:{settings.port}/docs")
    print()
    print("💡 配置信息:")
    print(f"   Redis: {settings.redis.host}:{settings.redis.port}/{settings.redis.db}")
    print(f"   OpenAI: {'✅ 已配置' if settings.openai.api_key else '❌ 未配置'}")
    print(f"   并发控制: 最大{settings.concurrency.max_concurrent_users}用户")
    print()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.monitoring.log_level.lower()
    )

if __name__ == "__main__":
    main() 