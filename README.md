# Agent Kit

一个用于开发和测试AI Agent的工具集合，包含提示词优化、MCP服务构建和Agent客户端实现。

## 项目结构

```
agent_kit/
├── prompt_tools/        # 提示词优化工具
├── MCP/                 # MCP服务示例集合
└── agent/              # Agent客户端实现（开发中）
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

### 3. Agent (智能代理，开发中)

计划实现一系列可以直接接入MCP服务的智能代理客户端。

计划功能：
- 通用Agent接口定义
- 多模型支持（Claude/OpenAI）
- 异步操作支持
- 完整的错误处理
- 会话管理
- 资源访问控制

## 环境要求

- Python 3.11+
- 依赖管理使用conda环境

## 快速开始

1. 创建conda环境：
```bash
conda create -n agent_kit python=3.11
conda activate agent_kit
```

2. 安装依赖：
```bash
# prompt_tools环境
conda env create -f prompt_tools/environment.yml

# MCP环境
conda env create -f MCP/environment.yml
```

3. 运行示例：
```bash
# 提示词优化示例
cd prompt_tools
python example.py

# MCP服务器示例
cd MCP/examples
python mcp_async.py  # 启动服务器
python client_demo.py  # 运行客户端测试
```

## 开发计划

- [x] 提示词优化工具基础功能
- [x] MCP基础示例实现
- [ ] 完善MCP服务器功能
- [ ] 实现通用Agent框架
- [ ] 添加更多模型支持
- [ ] 优化性能和并发处理
- [ ] 完善文档和测试用例

## 贡献指南

欢迎提交Issue和Pull Request。在提交代码前，请确保：
1. 代码风格符合项目规范
2. 添加了必要的测试用例
3. 更新了相关文档

## 许可证

MIT License
