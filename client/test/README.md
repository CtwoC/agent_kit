# 测试文件目录

这个目录包含了client模块的所有测试文件。

## 文件结构

```
client/test/
├── __init__.py          # 包初始化文件，设置Python路径
├── test_openai.py       # OpenAI客户端测试
├── test_claude.py       # Claude客户端测试
├── run_tests.py         # 测试运行脚本
└── README.md           # 本文件
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
python test_openai.py    # 运行OpenAI测试
python test_claude.py    # 运行Claude测试
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

## 特点

- ✅ 避免了相对导入的复杂性
- ✅ 保持了代码的清晰性和可读性
- ✅ 集中管理所有测试文件
- ✅ 提供了便捷的测试运行工具 