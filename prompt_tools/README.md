# Prompt Tools

用于优化和管理LLM Prompts的工具集。

## 项目结构

```
prompt_tools/
├── pyproject.toml      # 项目配置和依赖管理
├── requirements.txt    # pip依赖列表（可选，用于兼容性）
├── .env               # 环境变量配置
├── prompt_optimizer.py # 主要的prompt优化逻辑
├── prompt_templates.py # prompt模板定义
└── example.py         # 使用示例
```

## 安装

使用 uv（推荐）：
```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
uv pip install .
```

或使用传统的pip：
```bash
pip install -r requirements.txt
```

## 环境变量配置

在使用前，请确保在 `.env` 文件中配置了必要的API密钥：
```env
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here
```

## 使用示例

```python
from prompt_optimizer import PromptOptimizer

# 创建优化器实例（支持OpenAI或Claude）
optimizer = PromptOptimizer.create("openai")

# 优化prompt
result = optimizer.optimize(
    original_prompt="你的原始prompt",
    optimization_suggestions="优化建议"
)

# 使用自定义API端点
custom_optimizer = PromptOptimizer.create(
    "openai",
    base_url="https://your-custom-endpoint/v1"
)
```
