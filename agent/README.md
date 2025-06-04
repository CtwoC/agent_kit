# Agent Examples

这个目录包含各种Agent实现示例，展示如何使用OpenAI客户端构建不同类型的AI Agent服务。

## 📁 目录结构

```
agent/
├── examples/
│   ├── basic_agent/          # 基础Agent示例
│   │   ├── main.py           # FastAPI服务主文件
│   │   ├── requirements.txt  # Python依赖
│   │   ├── test_agent.py     # 测试脚本
│   │   └── README.md         # 详细说明
│   └── streaming_agent/      # 流式Agent示例
│       ├── main.py           # 流式FastAPI服务
│       ├── requirements.txt  # Python依赖
│       ├── test_agent.py     # 完整测试脚本
│       ├── simple_test.py    # 简单测试脚本
│       └── README.md         # 详细说明
└── README.md                 # 本文件
```

## 🚀 示例列表

### 1. 基础Agent (`examples/basic_agent/`)

最简单的Agent实现，包含：

- ✅ **FastAPI异步服务**
- ✅ **OpenAI GPT集成** 
- ✅ **系统提示词支持**
- ✅ **MCP工具支持**（可选）
- ✅ **使用统计**
- ❌ 无记忆功能
- ❌ 无CoT推理

**适用场景**：
- 简单的问答服务
- 快速原型开发
- 学习Agent基础架构

**启动方式**：
```bash
cd examples/basic_agent
python main.py
# 服务运行在 http://localhost:8080
```

### 2. 流式Agent (`examples/streaming_agent/`) ✨新增

支持实时流式响应的Agent实现，包含：

- ✅ **FastAPI异步服务**
- ✅ **流式响应** - Server-Sent Events (SSE)
- ✅ **OpenAI GPT集成** - 流式API
- ✅ **系统提示词支持**
- ✅ **MCP工具支持**（可选）
- ✅ **并发支持** - 多用户同时流式聊天
- ✅ **兼容性API** - 同时支持传统非流式API
- ✅ **使用统计**
- ❌ 无记忆功能
- ❌ 无CoT推理

**适用场景**：
- 实时聊天应用
- 长文本生成（写作助手）
- 代码生成（逐行展示）
- 创作工具（诗歌、故事）
- 教育应用（解释过程）

**启动方式**：
```bash
cd examples/streaming_agent
python main.py
# 服务运行在 http://localhost:8081
```

**快速测试**：
```bash
# 简单测试
python simple_test.py

# 完整测试
python test_agent.py
```

## 🔮 计划中的示例

### 3. 记忆Agent (`examples/memory_agent/`)
- 🔄 **对话记忆** - 维护用户对话历史
- 🔄 **会话管理** - 支持多用户会话
- 🔄 **数据持久化** - Redis/数据库存储

### 4. 思维链Agent (`examples/cot_agent/`) 
- 🔄 **思维链推理** - Step-by-step推理过程
- 🔄 **推理可视化** - 展示思考步骤
- 🔄 **复杂问题求解** - 多步骤问题分解

### 5. 工具Agent (`examples/tool_agent/`)
- 🔄 **丰富工具集** - 集成多种MCP工具
- 🔄 **工具编排** - 智能工具选择和组合
- 🔄 **错误恢复** - 工具调用失败处理

### 6. 企业级Agent (`examples/enterprise_agent/`)
- 🔄 **用户认证** - JWT/OAuth2
- 🔄 **权限控制** - RBAC
- 🔄 **限流监控** - 请求限制和监控
- 🔄 **日志审计** - 完整的操作日志

## 🛠️ 通用组件

所有示例都基于以下核心组件：

- **OpenAI客户端** (`../../client/openai_client.py`) - 统一的OpenAI API封装
- **基础客户端** (`../../client/base_client.py`) - LLM客户端基类
- **重试机制** (`../../client/utils/retry.py`) - 强健的重试装饰器
- **MCP工具集成** - 可选的工具调用能力

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository>
cd agent_kit

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="http://43.130.31.174:8003/v1"  # 可选
export MCP_URL="http://39.103.228.66:8165/mcp/"        # 可选
```

### 2. 选择示例

```bash
# 基础Agent - 简单问答
cd agent/examples/basic_agent
python main.py

# 流式Agent - 实时交互
cd agent/examples/streaming_agent  
python main.py
```

### 3. 测试服务

```bash
# 基础Agent测试
cd agent/examples/basic_agent
python test_agent.py

# 流式Agent测试
cd agent/examples/streaming_agent
python simple_test.py  # 简单测试
python test_agent.py   # 完整测试
```

## 📊 性能对比

| 示例 | 响应方式 | 延迟 | 内存使用 | 用户体验 | 适用场景 |
|------|----------|------|----------|----------|----------|
| 基础Agent | 一次性返回 | 低 | 低 | 需等待 | 问答、原型 |
| 流式Agent | 实时流式 | 很低 | 低 | 立即反馈 | 实时交互 |
| 记忆Agent | 一次性返回 | 中 | 中 | 上下文连续 | 对话应用 |
| 思维链Agent | 逐步展示 | 高 | 中 | 透明推理 | 复杂推理 |
| 工具Agent | 混合模式 | 中 | 中 | 功能丰富 | 任务执行 |
| 企业级Agent | 混合模式 | 中 | 高 | 企业级 | 生产环境 |

## 🔧 自定义开发

### 创建新示例

1. 在 `examples/` 下创建新目录
2. 复制现有示例作为模板：
   - `basic_agent/` - 适合简单功能
   - `streaming_agent/` - 适合实时交互
3. 修改 `main.py` 实现自定义逻辑
4. 更新 `requirements.txt` 添加新依赖
5. 编写 `README.md` 说明文档

### 扩展现有示例

- 修改系统提示词
- 添加新的API端点
- 集成额外的工具
- 增强错误处理
- 添加监控和日志

## 🐛 故障排除

### 常见问题

1. **OpenAI API密钥问题**
   ```bash
   export OPENAI_API_KEY="your-valid-api-key"
   ```

2. **端口占用**
   ```bash
   # 修改main.py中的端口配置
   uvicorn.run("main:app", port=8082)
   ```

3. **依赖冲突**
   ```bash
   # 使用虚拟环境
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

4. **MCP连接失败**
   ```bash
   # 检查MCP服务器状态
   curl http://39.103.228.66:8165/mcp/
   ```

5. **流式响应问题**
   - 确认浏览器支持SSE
   - 检查代理配置
   - 验证防火墙设置

## 📚 学习路径

推荐的学习顺序：

1. **基础Agent** - 理解基本架构 ⭐
2. **流式Agent** - 掌握实时交互 ⭐
3. **记忆Agent** - 学习状态管理
4. **工具Agent** - 掌握工具集成
5. **思维链Agent** - 复杂推理实现
6. **企业级Agent** - 生产级实践

## 🤝 贡献指南

欢迎贡献新的Agent示例！

1. Fork项目
2. 创建新的示例目录
3. 实现功能并测试
4. 编写文档
5. 提交Pull Request

## �� 许可证

本项目仅供学习和参考使用。 