from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
import openai
import anthropic
from prompt_templates import PROMPT_OPTIMIZER_SYSTEM, PROMPT_OPTIMIZER_USER_TEMPLATE

# 加载环境变量
load_dotenv()

class BaseOptimizer(ABC):
    """优化器的抽象基类"""
    
    @abstractmethod
    def optimize(
        self,
        original_prompt: str,
        optimization_suggestions: str,
        **kwargs
    ) -> str:
        """
        优化prompt的方法
        
        Args:
            original_prompt: 原始prompt内容
            optimization_suggestions: 优化建议（包含反馈和改进要求）
            **kwargs: 其他可选参数
            
        Returns:
            str: 优化后的prompt
        """
        pass

class OpenAIOptimizer(BaseOptimizer):
    """使用OpenAI API的优化器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化OpenAI优化器
        
        Args:
            api_key: OpenAI API密钥，如果不提供则从环境变量获取
            base_url: API基础URL，用于自定义端点或代理服务
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API密钥未提供")
        
        # 配置OpenAI客户端
        openai.api_key = self.api_key
        if base_url:
            openai.base_url = base_url

    def optimize(
        self,
        original_prompt: str,
        optimization_suggestions: str,
        model: str = "gpt-4o",
        temperature: float = 0.7
    ) -> str:
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": PROMPT_OPTIMIZER_SYSTEM},
                    {"role": "user", "content": PROMPT_OPTIMIZER_USER_TEMPLATE.format(
                        original_prompt=original_prompt,
                        optimization_suggestions=optimization_suggestions
                    )}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI优化过程中出现错误: {str(e)}")

class ClaudeOptimizer(BaseOptimizer):
    """使用Anthropic Claude API的优化器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化Claude优化器
        
        Args:
            api_key: Anthropic API密钥，如果不提供则从环境变量获取
            base_url: API基础URL，用于自定义端点或代理服务
        """
        # 获取API密钥
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 Anthropic API 密钥，请在环境变量中设置 ANTHROPIC_API_KEY 或直接传入")

        # 配置Anthropic客户端
        if base_url:
            os.environ["ANTHROPIC_API_BASE"] = base_url
        
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def optimize(
        self,
        original_prompt: str,
        optimization_suggestions: str,
        model: str = "claude-3-7-sonnet-20250219"
    ) -> str:
        try:
            # 构建prompt
            prompt = PROMPT_OPTIMIZER_USER_TEMPLATE.format(
                original_prompt=original_prompt,
                optimization_suggestions=optimization_suggestions
            )

            prompt = PROMPT_OPTIMIZER_SYSTEM + "\n\n" + prompt

            # 调用API
            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # 返回优化后的prompt
            return response.content[0].text

        except Exception as e:
            raise Exception(f"Claude优化过程中出现错误: {str(e)}")

class PromptOptimizer:
    """Prompt优化器工厂类"""
    
    OPTIMIZERS = {
        "openai": OpenAIOptimizer,
        "claude": ClaudeOptimizer
    }
    
    @staticmethod
    def create(provider: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> BaseOptimizer:
        """
        创建指定提供商的优化器实例
        
        Args:
            provider: 优化器提供商 ("openai" 或 "claude")
            api_key: 可选的API密钥
            base_url: 可选的API基础URL，用于自定义端点或代理服务
            
        Returns:
            BaseOptimizer: 优化器实例
        """
        if provider not in PromptOptimizer.OPTIMIZERS:
            raise ValueError(f"不支持的优化器提供商: {provider}")
        
        return PromptOptimizer.OPTIMIZERS[provider](api_key=api_key, base_url=base_url)

if __name__ == "__main__":
    prompt = "请帮我写一篇关于人工智能的文章"
    optimizer = PromptOptimizer.create("claude")
    optimized_prompt = optimizer.optimize(prompt,"优化这个prompt,使得要求更详细")
    print(optimized_prompt)
