#!/usr/bin/env python3
"""
流式Agent服务 - 主应用入口
负责FastAPI路由和API端点管理
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn

# 导入自定义模块
from load_user import user_manager
from chat_processor import ChatProcessor

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🚀 启动模块化流式Agent服务...")
    yield
    print("🔄 正在关闭流式Agent服务...")

# 创建FastAPI应用
app = FastAPI(
    title="模块化流式Agent服务",
    description="支持用户级并发控制的模块化流式聊天Agent",
    version="3.0.0",
    lifespan=lifespan
)

# 请求模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    uid: str  # 用户唯一标识符
    system_prompt: Optional[str] = None  # 可选的自定义系统提示词

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "模块化流式Agent服务",
        "version": "3.0.0",
        "features": ["流式聊天", "工具调用", "用户级并发控制", "模块化设计"],
        "endpoints": ["/chat/stream", "/chat", "/health", "/stats"],
        "modules": ["load_user", "chat_processor", "main"]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    processing_info = await user_manager.get_processing_users()
    
    return {
        "status": "healthy", 
        "service": "modular_streaming_agent",
        "active_users": processing_info["active_users"],
        "processing_users": processing_info["processing_users"]
    }

@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """
    流式聊天端点
    
    Args:
        request: 包含用户消息、uid和可选系统提示词的请求
        
    Returns:
        Server-Sent Events流式响应
    """
    uid = request.uid
    
    # 检查用户是否已在处理中
    can_process = await user_manager.check_and_mark_user_processing(uid)
    
    if not can_process:
        error_msg = f"用户 {uid} 有请求正在处理中，请等待完成后再试"
        print(f"⚠️ {error_msg}")
        
        # 返回错误的流式响应
        async def error_response():
            import json
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg, 'uid': uid}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            error_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    # 处理流式聊天请求
    async def stream_with_cleanup():
        """带清理的流式响应生成器"""
        try:
            async for chunk in ChatProcessor.process_stream_chat(
                request.message, 
                uid, 
                request.system_prompt
            ):
                yield chunk
        finally:
            # 确保取消用户处理标记
            await user_manager.unmark_user_processing(uid)
    
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

@app.post("/chat")
async def chat_non_stream(request: ChatRequest):
    """
    非流式聊天端点
    
    Args:
        request: 包含用户消息、uid和可选系统提示词的请求
        
    Returns:
        完整的响应JSON
    """
    uid = request.uid
    
    # 检查用户是否已在处理中
    can_process = await user_manager.check_and_mark_user_processing(uid)
    
    if not can_process:
        raise HTTPException(
            status_code=429, 
            detail=f"用户 {uid} 有请求正在处理中，请等待完成后再试"
        )
    
    try:
        # 处理非流式聊天请求
        response = await ChatProcessor.process_chat(
            request.message, 
            uid, 
            request.system_prompt
        )
        return response
        
    except Exception as e:
        print(f"❌ 用户 {uid} 处理非流式聊天请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")
    
    finally:
        # 确保取消用户处理标记
        await user_manager.unmark_user_processing(uid)

@app.get("/stats")
async def get_stats():
    """获取当前处理状态统计"""
    processing_info = await user_manager.get_processing_users()
    
    return {
        "service_stats": {
            "active_users": processing_info["active_users"],
            "processing_users": processing_info["processing_users"]
        }
    }

if __name__ == "__main__":
    print("🌊 启动模块化用户级并发控制的流式Agent服务...")
    print("📖 请确保设置了以下环境变量:")
    print("   - OPENAI_API_KEY: OpenAI API密钥")
    print("   - MCP_URL: MCP服务器URL (可选)")
    print("   - OPENAI_BASE_URL: OpenAI API基础URL (可选)")
    print()
    print("🔗 流式API端点: POST /chat/stream")
    print("🔗 传统API端点: POST /chat") 
    print("🔗 健康检查: GET /health")
    print("🔗 统计信息: GET /stats")
    print("📝 注意: 现在需要在请求中包含 uid 参数")
    print()
    print("📦 模块结构:")
    print("   - load_user.py: 用户状态管理")
    print("   - chat_processor.py: 聊天逻辑处理")
    print("   - main.py: FastAPI应用主体")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    ) 