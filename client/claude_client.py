"""Claude API 客户端"""
from typing import Dict, Any, AsyncIterator, List, Optional
from datetime import datetime
from anthropic import AsyncAnthropic
from base_client import BaseLLMClient, Tool

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
        self.current_conversation = ""
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
            
    def _format_assistant_content(self, content: List[Dict[str, Any]]) -> str:
        """格式化助手的回复内容
        
        Args:
            content: 助手回复的原始内容列表
            
        Returns:
            格式化后的字符串
        """
        result = ""
        for block in content:
            if block["type"] == "text":
                result += block["text"]
            elif block["type"] == "tool_use":
                result += f"\n[Tool Call: {block['name']}]\n{block['input']}\n"
        return result.strip()
    
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
        # 更新当前对话内容
        if self.current_conversation:
            self.current_conversation += f"\nUser: {content}\n"
        else:
            self.current_conversation = f"User: {content}\n"
        
        while True:
            # 创建消息格式
            messages = [{"role": "user", "content": self.current_conversation}]
            
            # 创建流式会话
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,
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
                
                # 更新对话内容，添加助手的回复
                assistant_text = "Assistant: " + self._format_assistant_content(current_assistant_content)
                self.current_conversation += assistant_text + "\n"
                
                if not tool_calls:
                    # 没有工具调用，对话结束
                    break
                    
                # 处理工具调用
                tool_result = await self._process_tool_call(tool_calls[0])
                if tool_result:
                    # 添加工具调用结果到对话内容
                    tool_text = f"Tool ({tool_result.tool_name}): {tool_result.tool_result}\n"
                    self.current_conversation += tool_text
                else:
                    # 工具调用失败，结束对话
                    break
