"""Claude API 客户端"""
from typing import Dict, Any, AsyncIterator, List, Optional
from datetime import datetime
from anthropic import AsyncAnthropic
from base_client import BaseLLMClient

class ToolResult:
    """Tool 调用结果"""
    def __init__(self, tool_name: str, tool_result: Any, timestamp: str = None):
        self.tool_name = tool_name
        self.tool_result = tool_result
        self.timestamp = timestamp or datetime.now().isoformat()

class ClaudeClient(BaseLLMClient):
    """Claude API 客户端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        max_tokens: int = 4096,
        max_history_messages: int = 6,  # 保留的历史消息数量
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        # 初始化 Claude 客户端
        self.model = model
        self.max_tokens = max_tokens
        self.max_history_messages = max_history_messages
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=self.llm_base_url,  # 如果为 None，使用默认的 API URL
        )
        
        # 对话状态
        self.message_history: List[Dict[str, Any]] = []
        self.tool_results: List[ToolResult] = []

    async def _process_tool_call(self, tool_call: Dict[str, Any]) -> Optional[ToolResult]:
        """处理工具调用
        
        Args:
            tool_call: 工具调用信息
            
        Returns:
            工具调用结果
        """
        tool_name = tool_call["name"]
        tool_input = tool_call["input"]
        
        # 调用 MCP 工具
        try:
            result = await self.call_mcp_tool(
                tool_name=tool_name,
                params=tool_input
            )
            
            # 保存工具调用结果
            tool_result = ToolResult(tool_name, result)
            self.tool_results.append(tool_result)
            return tool_result
            
        except Exception as e:
            print(f"Tool call failed: {str(e)}")
            return None
            
    def _convert_tools_for_claude(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """将工具列表转换为 Claude 格式"""
        return [{
            "type": "custom",
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        } for tool in tools]
    
    async def chat_stream(self, content: str) -> AsyncIterator[Dict[str, Any]]:
        """多轮对话和工具调用的流式处理
        
        Args:
            content: 当前轮次的对话内容
            tools: 可用的工具列表
            
        Yields:
            流式响应的 chunks
        """
        # 添加用户消息
        self.message_history.append({"role": "user", "content": content})
        
        while True:
            # 取最近的几条历史消息
            recent_messages = self.message_history[-self.max_history_messages:]
            
            # 创建流式会话
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=recent_messages,
                tools=self._convert_tools_for_claude(self.get_available_tools()),
            ) as stream:
                # 处理文本流
                current_assistant_content = []
                
                async for chunk in self._handle_stream(stream):
                    # 输出原始 chunk
                    yield chunk.model_dump()
                    
                # 获取完整消息
                final_message = await stream.get_final_message()
                message_json = final_message.model_dump()
                
                # 收集助手的回复内容
                current_assistant_content.extend(message_json["content"])
                
                # 检查工具调用
                tool_calls = [block for block in message_json["content"] if block["type"] == "tool_use"]
                
                if not tool_calls:
                    # 没有工具调用，对话结束
                    self.message_history.append({
                        "role": "assistant",
                        "content": current_assistant_content
                    })
                    break
                    
                # 处理工具调用
                tool_result = await self._process_tool_call(tool_calls[0])
                if tool_result:
                    # 添加工具调用结果到历史消息
                    self.message_history.append({
                        "role": "tool",
                        "content": tool_result.tool_result,
                        "tool_name": tool_result.tool_name,
                        "tool_call_id": tool_calls[0]["id"]
                    })
                else:
                    # 工具调用失败，结束对话
                    break
