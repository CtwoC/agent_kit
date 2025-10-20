# 测试文件目录

这个目录包含了client模块的所有测试文件。

## 文件结构

```
client/test/
├── __init__.py                    # 包初始化文件，设置Python路径
├── test_openai.py                 # OpenAI客户端测试
├── test_claude.py                 # Claude客户端测试
├── test_openai_chat.py            # OpenAI对话功能测试
├── test_url_fix.py                # URL修复测试
├── debug_tools.py                 # 调试工具
├── test_qwen_compatibility.py     # Qwen兼容性完整测试（使用OpenAI client）
├── quick_qwen_test.py             # Qwen兼容性快速测试（使用OpenAI client）
├── test_qwen_client.py            # 专用QwenClient测试
├── QWEN_COMPATIBILITY.md          # Qwen兼容性说明文档
└── README.md                      # 本文件
```

## 路径设置

为了避免使用相对导入（`from .xxx import`），我们使用了以下方法：

1. 在每个测试文件开头添加路径设置：
   ```python
   import sys
   import os
   # 添加client目录到Python路径
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```

2. 这样就可以直接使用绝对导入：
   ```python
   from openai_client import OpenAIClient
   from claude_client import ClaudeClient
   ```

## 运行测试

### 直接运行单个测试

```bash
cd client/test
python test_openai.py              # 运行OpenAI测试
python test_claude.py              # 运行Claude测试
python test_qwen_compatibility.py  # 运行Qwen兼容性完整测试（使用OpenAI client）
python quick_qwen_test.py          # 运行Qwen兼容性快速测试（使用OpenAI client）
python test_qwen_client.py         # 运行专用QwenClient测试
```

### 使用测试运行脚本

```bash
cd client/test
python run_tests.py openai   # 运行OpenAI测试
python run_tests.py claude   # 运行Claude测试
python run_tests.py all      # 运行所有测试
```

## 环境要求

运行测试前请确保设置了相应的环境变量：

- `OPENAI_API_KEY`: OpenAI API密钥（运行OpenAI测试时需要）
- `ANTHROPIC_API_KEY`: Anthropic API密钥（运行Claude测试时需要）
- `QWEN_API_KEY`: Qwen API密钥（运行Qwen兼容性测试时需要）
- `QWEN_BASE_URL`: Qwen API端点（可选，默认为 `https://dashscope.aliyuncs.com/compatible-mode/v1`）
- `QWEN_MODEL`: Qwen模型名称（可选，默认为 `qwen-plus`）

## Qwen API 测试

我们提供了两种方式来使用 Qwen API：

### 方式1: 使用 OpenAI client（兼容模式）
通过设置 `base_url` 参数，让 OpenAI client 兼容 Qwen API：

```bash
# 快速测试
python quick_qwen_test.py

# 完整兼容性测试
python test_qwen_compatibility.py
```

### 方式2: 使用专用 QwenClient（推荐）
专门为 Qwen API 设计的客户端，流式响应使用标准 Chat Completions API：

```bash
# 测试专用 QwenClient
python test_qwen_client.py
```

### 两种方式的对比

| 特性 | OpenAI client + base_url | 专用 QwenClient |
|------|-------------------------|-----------------|
| 非流式对话 | ✅ Chat Completions API | ✅ Chat Completions API |
| 流式对话 | ❌ Response API（Qwen不支持） | ✅ Chat Completions API (stream=True) |
| 兼容性 | 通用兼容 | 专门优化 |
| 推荐场景 | 多API提供商 | 主要使用Qwen |

详细的兼容性说明请参考 [QWEN_COMPATIBILITY.md](./QWEN_COMPATIBILITY.md)

## 特点

- ✅ 避免了相对导入的复杂性
- ✅ 保持了代码的清晰性和可读性
- ✅ 集中管理所有测试文件
- ✅ 提供了便捷的测试运行工具 