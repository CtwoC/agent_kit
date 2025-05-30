"""OpenAI API 客户端"""
from typing import Dict, Any, AsyncIterator, List
from openai import AsyncOpenAI
from base_client import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    """OpenAI API 客户端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        # 初始化 OpenAI 客户端
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.llm_base_url,  # 如果为 None，使用默认的 API URL
        )

    async def chat(self, content: str, **kwargs) -> Dict[str, Any]:
        """非流式对话"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": content}
            ],
            **kwargs
        )
        return response.model_dump()

    async def stream_chat(self, content: str, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """流式对话"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": content}
            ],
            stream=True,
            **kwargs
        )
        
        async for chunk in self._handle_stream(stream):
            yield chunk.model_dump()

    async def tool_call(self, content: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """工具调用"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": content}
            ],
            tools=tools,
            **kwargs
        )
        return response.model_dump()

    async def stream_tool_call(self, content: str, tools: List[Dict], **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """流式工具调用"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": content}
            ],
            tools=tools,
            stream=True,
            **kwargs
        )
        
        async for chunk in self._handle_stream(stream):
            yield chunk.model_dump()
