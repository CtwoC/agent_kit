# Agent Kit

一个用于开发和测试AI Agent的工具集合，包含提示词优化、MCP服务构建、LLM客户端和Agent服务实现。

## 项目结构

```
agent_kit/
├── prompt_tools/        # 提示词优化工具
├── MCP/                 # MCP服务示例集合
├── client/             # LLM客户端实现
└── agent/              # Agent服务示例
```

## 功能模块

### 1. Prompt Tools (提示词优化工具)

提供了一套完整的提示词优化和测试工具，支持多种大语言模型。

主要功能：
- 提示词自动优化
- 多模型对比测试
- 优化结果可视化
- 支持OpenAI和Claude等模型

使用示例见 `prompt_tools/example.py`

### 2. MCP (Machine Communication Protocol)

包含多个MCP服务器和客户端的实现示例，展示了MCP协议的各种使用场景。

特性：
- 同步/异步服务器实现
- 完整的客户端测试用例
- 支持工具注册和调用
- 资源管理示例
- 批量操作支持

目录结构：
```
MCP/
├── examples/           # 示例代码
│   ├── mcp_async.py   # 异步服务器示例
│   ├── mcp_sync.py    # 同步服务器示例
│   └── client_demo.py # 客户端测试示例
├── server/            # 服务器实现（开发中）
└── client/           # 客户端实现（开发中）
```

### 3. Client (LLM客户端)

统一的LLM客户端实现，支持多种大语言模型和MCP工具集成。

特性：
- **多模型支持** - OpenAI GPT、Claude等
- **MCP工具集成** - 自动发现和调用MCP工具
- **异步操作** - 完全异步实现，高性能
- **重试机制** - 智能重试，提高稳定性
- **流式响应** - 支持流式和非流式响应
- **使用统计** - Token使用和成本跟踪
- **错误处理** - 完善的错误处理机制

目录结构：
```
client/
├── base_client.py      # LLM客户端基类
├── openai_client.py    # OpenAI客户端实现
├── claude_client.py    # Claude客户端实现
├── utils/              # 工具模块
│   └── retry.py        # 重试装饰器
├── exceptions.py       # 异常定义
└── test/              # 测试用例
    ├── test_openai.py
    ├── test_claude.py
    └── debug_tools.py
```

### 4. Agent (智能代理服务)

基于LLM客户端构建的各种Agent服务示例，展示不同的应用场景。

特性：
- **FastAPI服务** - 高性能异步Web API
- **多种Agent类型** - 从基础到企业级的各种实现
- **完整示例** - 开箱即用的服务实现
- **详细文档** - 每个示例都有完整说明

目录结构：
```
agent/
├── examples/
│   └── basic_agent/    # 基础Agent示例
│       ├── main.py     # FastAPI服务
│       ├── test_agent.py # 测试脚本
│       └── README.md   # 详细说明
└── README.md          # Agent总体说明
```

**当前示例**：
- ✅ **基础Agent** - 最简单的问答服务
- 🔄 **记忆Agent** - 带对话记忆的Agent
- 🔄 **思维链Agent** - 支持复杂推理的Agent
- 🔄 **工具Agent** - 集成丰富工具的Agent
- 🔄 **流式Agent** - 实时交互Agent
- 🔄 **企业级Agent** - 生产级Agent实现

## 环境要求

- Python 3.11+
- 依赖管理使用conda或pip

## 快速开始

### 1. 环境准备

```bash
# 使用conda（推荐）
conda create -n agent_kit python=3.11
conda activate agent_kit

# 或使用pip + venv
python -m venv agent_kit
source agent_kit/bin/activate  # Linux/Mac
# 或 agent_kit\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
# 基础依赖
pip install fastapi uvicorn openai anthropic fastmcp

# 可选：提示词工具
pip install -r prompt_tools/requirements.txt

# 可选：Agent示例依赖
pip install -r agent/examples/basic_agent/requirements.txt
```

### 3. 设置环境变量

```bash
# 必需
export OPENAI_API_KEY="your-openai-api-key"

# 可选
export ANTHROPIC_API_KEY="your-claude-api-key"
export OPENAI_BASE_URL="http://43.130.31.174:8003/v1"
export MCP_URL="http://39.103.228.66:8165/mcp/"
```

### 4. 运行示例

```bash
# 测试LLM客户端
cd client/test
python test_openai.py

# 启动基础Agent服务
cd agent/examples/basic_agent
python main.py

# 测试Agent服务
python test_agent.py
```

## 使用示例

### LLM客户端使用

```python
from client.openai_client import OpenAIClient

async def example():
    async with OpenAIClient(
        api_key="your-key",
        mcp_urls=["http://localhost:8165/mcp/"]
    ) as client:
        # 简单对话
        response = await client.chat("你好，世界！")
        print(response["choices"][0]["message"]["content"])
        
        # 流式对话
        async for chunk in client.stream_chat("写一首诗"):
            print(chunk, end="")
```

### Agent服务使用

```bash
# 启动服务
python agent/examples/basic_agent/main.py

# 测试请求
curl -X POST "http://localhost:8080/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "你好！"}'
```

## 开发计划

- [x] 提示词优化工具基础功能
- [x] MCP基础示例实现
- [x] **LLM客户端统一实现**
- [x] **基础Agent服务示例**
- [ ] 记忆Agent实现
- [ ] 思维链Agent实现  
- [ ] 工具Agent实现
- [ ] 流式Agent实现
- [ ] 企业级Agent实现
- [ ] 完善MCP服务器功能
- [ ] 优化性能和并发处理
- [ ] 完善文档和测试用例

## 贡献指南

欢迎提交Issue和Pull Request。在提交代码前，请确保：
1. 代码风格符合项目规范
2. 添加了必要的测试用例
3. 更新了相关文档

## 许可证

MIT License
