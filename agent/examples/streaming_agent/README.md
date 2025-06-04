# 流式Agent示例

这是一个支持**实时流式响应**的FastAPI异步Agent服务示例，使用Server-Sent Events (SSE)技术实现流式传输。

## 功能特性

- ✅ **FastAPI异步服务** - 高性能的异步Web API
- ✅ **流式响应** - 实时Server-Sent Events流式传输
- ✅ **OpenAI GPT集成** - 使用GPT模型流式API
- ✅ **系统提示词** - 支持默认和自定义系统提示词
- ✅ **MCP工具支持** - 可选的MCP工具集成
- ✅ **并发支持** - 支持多个并发流式请求
- ✅ **兼容性API** - 同时提供传统非流式API
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

服务将在 `http://localhost:8081` 启动。

## API端点

### POST /chat/stream （主要）

发送消息给Agent并获取流式响应。

**请求示例：**
```json
{
    "message": "写一首关于春天的诗",
    "system_prompt": "你是一个诗人"  // 可选
}
```

**流式响应示例：**
```
data: {"type": "start", "message": "开始生成响应..."}

data: {"type": "content", "chunk": "春"}

data: {"type": "content", "chunk": "风"}

data: {"type": "content", "chunk": "拂"}

...

data: {"type": "complete", "full_content": "春风拂面...", "usage": {...}}
```

### POST /chat （兼容性）

传统的非流式API，一次性返回完整响应。

### GET /

服务状态检查。

### GET /health

健康检查端点，返回流式支持状态。

### GET /stats

获取使用统计信息。

### POST /reset-stats

重置使用统计。

## 流式响应格式

流式响应使用Server-Sent Events (SSE)格式，每行以`data: `开头，包含JSON数据：

### 响应类型

1. **开始事件** (`type: "start"`)
   ```json
   {"type": "start", "message": "开始生成响应..."}
   ```

2. **内容块** (`type: "content"`)
   ```json
   {"type": "content", "chunk": "响应的一部分文字"}
   ```

3. **完成事件** (`type: "complete"`)
   ```json
   {
     "type": "complete",
     "full_content": "完整响应内容",
     "usage": {
       "input_tokens": 45,
       "output_tokens": 120,
       "total_tokens": 165,
       "total_cost": 0.00033
     }
   }
   ```

4. **错误事件** (`type: "error"`)
   ```json
   {"type": "error", "error": "错误描述"}
   ```

## 使用示例

### JavaScript前端集成

```javascript
const eventSource = new EventSource('/chat/stream', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: '写一首诗'
    })
});

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'start':
            console.log('开始生成...');
            break;
        case 'content':
            document.getElementById('output').innerHTML += data.chunk;
            break;
        case 'complete':
            console.log('生成完成', data.usage);
            eventSource.close();
            break;
        case 'error':
            console.error('错误:', data.error);
            eventSource.close();
            break;
    }
};
```

### Python客户端

```python
import requests
import json

def stream_chat(message):
    response = requests.post(
        'http://localhost:8081/chat/stream',
        json={'message': message},
        stream=True
    )
    
    for line in response.iter_lines():
        if line and line.startswith(b'data: '):
            data = json.loads(line[6:])
            
            if data['type'] == 'content':
                print(data['chunk'], end='', flush=True)
            elif data['type'] == 'complete':
                print(f"\n完成! 使用了{data['usage']['total_tokens']}个tokens")

stream_chat("写一个Python函数")
```

### cURL测试

```bash
curl -X POST "http://localhost:8081/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "你好，世界！"}' \
     --no-buffer
```

## 测试

### 运行完整测试

```bash
python test_agent.py
```

测试包含：
- ✅ 健康检查
- ✅ 流式聊天测试（4个测试用例）
- ✅ 非流式兼容性测试
- ✅ 并发流式请求测试
- ✅ 使用统计检查

### 手动测试

```bash
# 测试流式API
curl -X POST "http://localhost:8081/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "写一首关于技术的诗"}' \
     --no-buffer

# 测试兼容性API
curl -X POST "http://localhost:8081/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "你好"}'
```

## 性能特点

### 优势

1. **实时响应** - 用户可以立即看到内容生成
2. **更好的用户体验** - 避免长时间等待
3. **并发支持** - 支持多个用户同时使用
4. **资源高效** - 流式传输减少内存占用
5. **可中断** - 用户可以随时停止接收

### 适用场景

- 💬 **聊天应用** - 实时对话体验
- ✍️ **写作助手** - 长文本生成
- 📝 **代码生成** - 代码逐行展示
- 🎨 **创作工具** - 诗歌、故事创作
- 📚 **教育应用** - 解释过程展示

## 与基础Agent的对比

| 特性 | 基础Agent | 流式Agent |
|------|----------|----------|
| 响应方式 | 一次性返回 | 实时流式 |
| 用户体验 | 需要等待 | 立即反馈 |
| 并发能力 | 好 | 更好 |
| 复杂度 | 简单 | 中等 |
| 适用场景 | 简单问答 | 实时交互 |
| 端口 | 8080 | 8081 |

## 部署建议

### 生产环境

```bash
uvicorn main:app --host 0.0.0.0 --port 8081 --workers 4
```

### 代理配置

如果使用Nginx等代理，需要特殊配置支持SSE：

```nginx
location /chat/stream {
    proxy_pass http://backend;
    proxy_set_header Cache-Control no-cache;
    proxy_set_header Connection keep-alive;
    proxy_buffering off;
    proxy_read_timeout 300s;
}
```

## 扩展建议

基于这个流式示例，你可以：

1. **添加WebSocket支持** - 双向实时通信
2. **添加流式工具调用** - 工具调用过程可视化
3. **添加中断机制** - 用户可以停止生成
4. **添加多轮对话** - 保持对话上下文
5. **添加进度指示** - 显示生成进度
6. **添加类型化响应** - 支持不同数据类型

## 故障排除

1. **流式响应中断**
   - 检查网络连接稳定性
   - 确认代理配置支持SSE

2. **并发性能问题**
   - 调整uvicorn workers数量
   - 优化OpenAI API调用频率

3. **内存使用过高**
   - 监控并发请求数量
   - 实现请求限流机制

## 许可证

本示例仅供学习和参考使用。 