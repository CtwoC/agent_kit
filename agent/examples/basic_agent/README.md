# 基础Agent示例

这是一个最简单的FastAPI异步Agent服务示例，使用OpenAI GPT模型处理用户请求。

## 功能特性

- ✅ **FastAPI异步服务** - 高性能的异步Web API
- ✅ **OpenAI GPT集成** - 使用GPT模型生成响应
- ✅ **系统提示词** - 支持默认和自定义系统提示词
- ✅ **MCP工具支持** - 可选的MCP工具集成
- ✅ **使用统计** - Token使用和成本统计
- ✅ **健康检查** - 服务状态监控
- ❌ **无记忆功能** - 每次请求独立处理
- ❌ **无CoT推理** - 不包含思维链功能

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
# 必需
export OPENAI_API_KEY="your-openai-api-key"

# 可选 - 自定义OpenAI API基础URL
export OPENAI_BASE_URL="http://43.130.31.174:8003/v1"

# 可选 - MCP服务器URL
export MCP_URL="http://39.103.228.66:8165/mcp/"
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8080` 启动。

## API端点

### POST /chat

发送消息给Agent并获取响应。

**请求示例：**
```json
{
    "message": "你好，请介绍一下你自己",
    "system_prompt": "你是一个友好的AI助手"  // 可选
}
```

**响应示例：**
```json
{
    "response": "你好！我是一个AI助手，很高兴为您服务...",
    "usage": {
        "input_tokens": 45,
        "output_tokens": 120,
        "total_tokens": 165,
        "total_cost": 0.00033
    },
    "model": "gpt-4.1-2025-04-14"
}
```

### GET /

服务状态检查。

**响应示例：**
```json
{
    "message": "🤖 基础Agent服务运行中",
    "status": "healthy",
    "version": "1.0.0"
}
```

### GET /health

健康检查端点。

### GET /stats

获取使用统计信息。

### POST /reset-stats

重置使用统计。

## 使用示例

### cURL请求

```bash
curl -X POST "http://localhost:8080/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "什么是人工智能？"
     }'
```

### Python请求

```python
import requests

response = requests.post("http://localhost:8080/chat", json={
    "message": "请解释一下量子计算的基本概念"
})

print(response.json())
```

### JavaScript请求

```javascript
const response = await fetch('http://localhost:8080/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: '帮我写一首关于春天的诗'
    })
});

const data = await response.json();
console.log(data);
```

## 自定义配置

### 修改系统提示词

在代码中修改 `DEFAULT_SYSTEM_PROMPT` 变量，或在请求中传入 `system_prompt` 参数。

### 修改端口

在 `main.py` 的最后部分修改端口：

```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8081,  # 修改端口
    reload=True,
    log_level="info"
)
```

## 部署建议

### 生产环境

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Docker部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 错误处理

服务包含完整的错误处理机制：

- 环境变量验证
- OpenAI客户端初始化检查
- API调用异常处理
- HTTP状态码返回

## 扩展建议

基于这个基础示例，你可以：

1. **添加记忆功能** - 集成Redis或数据库存储对话历史
2. **添加流式响应** - 支持Server-Sent Events
3. **添加用户认证** - JWT或OAuth2集成
4. **添加限流功能** - 防止API滥用
5. **添加更多工具** - 集成更多MCP工具
6. **添加思维链** - 实现CoT推理功能

## 故障排除

1. **OpenAI客户端初始化失败**
   - 检查 `OPENAI_API_KEY` 环境变量
   - 验证API密钥有效性

2. **MCP连接失败**
   - 检查 `MCP_URL` 配置
   - 确认MCP服务器运行状态

3. **端口占用**
   - 修改端口配置
   - 检查其他服务占用

## 许可证

本示例仅供学习和参考使用。 