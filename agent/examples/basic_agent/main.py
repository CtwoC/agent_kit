#!/usr/bin/env python3
"""
基础Agent示例 - 最简单的FastAPI异步Agent服务

功能：
- 接收POST请求的用户提示词
- 使用系统提示词
- 调用OpenAI GPT模型
- 返回响应
- 没有记忆、CoT等其他功能
"""

import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

# 添加client目录到Python路径
# 当前文件位于: agent/examples/basic_agent/main.py
# 需要回到项目根目录，然后进入client目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
client_path = os.path.join(project_root, 'client')
sys.path.insert(0, client_path)

from openai_client import OpenAIClient

# 全局变量存储客户端
openai_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global openai_client
    
    # 启动时初始化OpenAI客户端
    print("🚀 初始化OpenAI客户端...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ 请设置环境变量 OPENAI_API_KEY")
    
    # MCP服务器配置（可选）
    mcp_url = os.getenv("MCP_URL", "http://39.103.228.66:8165/mcp/")
    base_url = os.getenv("OPENAI_BASE_URL", "http://43.130.31.174:8003/v1")
    
    openai_client = OpenAIClient(
        api_key=api_key,
        base_url=base_url,
        mcp_urls=[mcp_url] if mcp_url else None
    )
    
    # 进入上下文
    await openai_client.__aenter__()
    print("✅ OpenAI客户端初始化成功")
    
    yield
    
    # 关闭时清理资源
    print("🔄 正在关闭OpenAI客户端...")
    await openai_client.__aexit__(None, None, None)
    print("✅ OpenAI客户端已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="基础Agent服务",
    description="最简单的Agent示例 - 使用OpenAI GPT模型回答用户问题",
    version="1.0.0",
    lifespan=lifespan
)

# 请求模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    system_prompt: str = None  # 可选的自定义系统提示词

# 响应模型  
class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    usage: dict
    model: str

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """你是一个有用、诚实和无害的AI助手。

你的任务是：
1. 理解用户的问题或需求
2. 提供准确、有帮助的回答
3. 保持友好和专业的语气
4. 如果不确定答案，请诚实地说明

请用中文回答，除非用户明确要求使用其他语言。"""

@app.get("/")
async def root():
    """根路径 - 服务状态检查"""
    return {
        "message": "🤖 基础Agent服务运行中",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "client_initialized": openai_client is not None
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天端点 - 处理用户消息并返回AI响应
    
    Args:
        request: 包含用户消息和可选系统提示词的请求
        
    Returns:
        包含AI响应、使用统计和模型信息的响应
    """
    try:
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI客户端未初始化")
        
        # 构建完整的提示词
        system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT
        full_prompt = f"系统提示词：\n{system_prompt}\n\n用户消息：\n{request.message}"
        
        print(f"📝 收到用户消息: {request.message[:50]}{'...' if len(request.message) > 50 else ''}")
        
        # 调用OpenAI客户端
        response = await openai_client.chat(full_prompt)
        
        # 提取响应内容
        assistant_message = response["choices"][0]["message"]["content"]
        
        # 构建响应
        chat_response = ChatResponse(
            response=assistant_message,
            usage={
                "input_tokens": openai_client.usage.input_tokens,
                "output_tokens": openai_client.usage.output_tokens,
                "total_tokens": openai_client.usage.total_tokens,
                "total_cost": round(openai_client.usage.total_cost, 6)
            },
            model=response.get("model", "unknown")
        )
        
        print(f"✅ 响应生成成功，总计 {openai_client.usage.total_tokens} tokens")
        
        return chat_response
        
    except Exception as e:
        print(f"❌ 处理聊天请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

@app.get("/stats")
async def get_stats():
    """获取使用统计"""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI客户端未初始化")
        
    return {
        "usage_stats": {
            "input_tokens": openai_client.usage.input_tokens,
            "output_tokens": openai_client.usage.output_tokens, 
            "total_tokens": openai_client.usage.total_tokens,
            "input_cost": round(openai_client.usage.input_cost, 6),
            "output_cost": round(openai_client.usage.output_cost, 6),
            "total_cost": round(openai_client.usage.total_cost, 6)
        },
        "available_tools": len(openai_client.get_available_tools()) if openai_client else 0
    }

@app.post("/reset-stats")
async def reset_stats():
    """重置使用统计"""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI客户端未初始化")
        
    openai_client.usage.reset()
    return {"message": "使用统计已重置"}

if __name__ == "__main__":
    print("🚀 启动基础Agent服务...")
    print("📖 请确保设置了以下环境变量:")
    print("   - OPENAI_API_KEY: OpenAI API密钥")
    print("   - MCP_URL: MCP服务器URL (可选)")
    print("   - OPENAI_BASE_URL: OpenAI API基础URL (可选)")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    ) 