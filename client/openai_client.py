"""OpenAI API 客户端"""
import json
from dataclasses import dataclass
from openai import AsyncOpenAI
from typing import Dict, Any, AsyncIterator, List, Optional
from base_client import BaseLLMClient, Tool, Usage, ModelPrices
from utils.retry import async_retry, stream_async_retry

@dataclass
class ToolResult:
    """工具调用结果
    
    Args:
        tool_name: 工具名称
        tool_result: 工具调用结果
    """
    tool_name: str
    tool_result: Any

class OpenAIClient(BaseLLMClient):
    """OpenAI API 客户端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1",
        **kwargs
    ):
        # 将 LLM 相关参数从 kwargs 中分离出来
        mcp_kwargs = {}
        if 'mcp_urls' in kwargs:
            mcp_kwargs['mcp_urls'] = kwargs.pop('mcp_urls')
        if 'enable_timeout_retry' in kwargs:
            mcp_kwargs['enable_timeout_retry'] = kwargs.pop('enable_timeout_retry')
            
        super().__init__(api_key, **mcp_kwargs)
        # 初始化 OpenAI 客户端
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            **kwargs  # 直接透传其他参数给 SDK
        )

        # 对话状态
        self.current_conversation = ""  
        self.tool_results: List[ToolResult] = []
        
        # 初始化 usage 统计
        self.usage = Usage(
            input_price=ModelPrices.GPT41_INPUT_PRICE,
            output_price=ModelPrices.GPT41_OUTPUT_PRICE
        )

    def _convert_mcp_tools_to_openai_format(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """将 MCP 工具格式转换为 OpenAI 格式
        
        Args:
            tools: MCP 工具列表
            
        Returns:
            OpenAI 格式的工具列表
        """
        openai_tools = []
        for tool in tools:
            openai_tool = {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
            openai_tools.append(openai_tool)
        return openai_tools

    def _convert_mcp_tools_to_chat_format(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """将 MCP 工具格式转换为 Chat Completions API 格式
        
        Args:
            tools: MCP 工具列表
            
        Returns:
            Chat Completions API 格式的工具列表
        """
        chat_tools = []
        for tool in tools:
            chat_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            }
            chat_tools.append(chat_tool)
        return chat_tools

    async def _process_response_tool_call(self, output: Dict[str, Any]) -> Optional[ToolResult]:
        """处理非流式 Response API 中的工具调用

        Args:
            output: 工具调用信息，格式为 Response API 的格式

        Returns:
            工具调用结果
        """
        if output.get("type") != "function_call" or output.get("status") != "completed":
            return None

        tool_name = output.get("name")
        # 只处理 MCP 工具
        if not self.get_tool_by_name(tool_name):
            print(f"DEBUG: 跳过非 MCP 工具: {tool_name}")  # 调试信息
            return None

        tool_input = json.loads(output.get("arguments", "{}"))
        return await self._call_tool(tool_name, tool_input)
    
    async def _process_stream_tool_call(self, output: Dict[str, Any]) -> Optional[ToolResult]:
        """处理流式响应中的工具调用
        
        Args:
            output: 工具调用信息，格式为 response API 的格式
            
        Returns:
            工具调用结果
        """
        if output.get("type") != "function_call" or output.get("status") != "completed":
            return None
            
        tool_name = output.get("name")
        # 只处理 MCP 工具
        if not self.get_tool_by_name(tool_name):
            print(f"DEBUG: 跳过非 MCP 工具: {tool_name}")  # 调试信息
            return None
            
        tool_input = json.loads(output.get("arguments", "{}"))
        return await self._call_tool(tool_name, tool_input)
    
    async def _call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[ToolResult]:
        """执行工具调用
        
        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            
        Returns:
            工具调用结果
        """
        try:
            print(f"DEBUG: 开始调用工具 {tool_name}，参数: {tool_input}")
            result = await self.call_mcp_tool(
                tool_name=tool_name,
                params=tool_input
            )
            print(f"DEBUG: 工具 {tool_name} 调用成功，结果: {result}")
            
            # 保存工具调用结果
            tool_result = ToolResult(tool_name, result)
            self.tool_results.append(tool_result)
            return tool_result
            
        except Exception as e:
            print(f"ERROR: 工具调用最终失败 (所有重试都用完)")
            print(f"  工具名称: {tool_name}")
            print(f"  输入参数: {tool_input}")
            print(f"  最终异常: {type(e).__name__}: {str(e)}")
            return None

    def _extract_text_from_response_output(self, outputs: List[Dict[str, Any]]) -> str:
        """从 Response API 的 output 中提取文本内容

        Args:
            outputs: Response API 返回的 output 列表

        Returns:
            提取的文本内容
        """
        text_content = ""
        for output in outputs:
            if output.get("type") == "message":
                content_blocks = output.get("content", [])
                for block in content_blocks:
                    if block.get("type") == "text":
                        text_content += block.get("text", "")
        return text_content

    @async_retry(timeout=60.0)
    async def chat(self, content: str, **kwargs) -> Dict[str, Any]:
        """对话 - 使用 Response API（无状态模式）

        Args:
            content: 当前轮次的对话内容

        Returns:
            对话响应
        """
        print(f"DEBUG: chat开始处理用户输入: {content}")  # 调试信息

        # 更新当前对话内容（客户端管理状态）
        if self.current_conversation:
            self.current_conversation += f"\nUser: {content}\n"
        else:
            self.current_conversation = f"User: {content}\n"

        print(f"DEBUG: 当前对话内容:\n{self.current_conversation}")  # 调试信息

        # 循环处理，直到没有工具调用
        while True:
            # 获取可用工具列表
            tools = self.get_available_tools()
            mcp_tools = self._convert_mcp_tools_to_openai_format(tools)
            print(f"DEBUG: 可用工具数量: {len(tools)}")  # 调试信息

            # 合并用户传入的工具和 MCP 工具
            if 'tools' in kwargs:
                user_tools = kwargs.pop('tools')
                all_tools = mcp_tools + user_tools
            else:
                all_tools = mcp_tools

            print(f"DEBUG: 准备调用 Response API（无状态模式）...")  # 调试信息

            # 调用 Response API（无状态模式：store=False）
            response = await self.client.responses.create(
                model=self.model,
                input=[{"role": "user", "content": self.current_conversation}],
                tools=all_tools if all_tools else None,
                store=False,  # 🔑 关键：不使用服务端状态管理，保持客户端管理
                **kwargs
            )

            response_data = response.model_dump()
            print(f"DEBUG: 收到 Response API 响应")  # 调试信息

            # 更新usage统计（Response API 使用 input_tokens/output_tokens）
            if usage := response_data.get("usage"):
                self.usage.input_tokens += usage.get("input_tokens", 0)
                self.usage.output_tokens += usage.get("output_tokens", 0)
                print(f"DEBUG: 更新usage - 输入:{usage.get('input_tokens', 0)}, 输出:{usage.get('output_tokens', 0)}")

            # 处理 Response API 的输出格式
            outputs = response_data.get("output", [])

            # 提取文本内容
            assistant_content = self._extract_text_from_response_output(outputs)

            # 检查是否有工具调用
            has_tool_calls = False
            for output in outputs:
                if output.get("type") == "function_call":
                    print(f"DEBUG: 发现工具调用: {output.get('name')}")  # 调试信息
                    result = await self._process_response_tool_call(output)
                    if result:
                        has_tool_calls = True
                        # 添加工具调用结果到对话内容
                        tool_response = f"Tool <{result.tool_name}> returned: {result.tool_result}\n"
                        self.current_conversation += tool_response
                        print(f"DEBUG: 工具调用结果已添加到对话")

            # 添加助手回复到对话历史
            if assistant_content:
                self.current_conversation += f"Assistant: {assistant_content}\n"

            # 如果没有工具调用，返回响应
            if not has_tool_calls:
                print(f"DEBUG: 没有工具调用，对话结束")
                print(f"DEBUG: chat函数完成")
                return response_data
            else:
                print(f"DEBUG: 继续下一轮对话处理工具调用结果")
                # 继续循环处理工具调用结果

    @stream_async_retry(max_retries=3, chunk_timeout=60.0)
    async def stream_chat(self, content: str, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """流式对话和工具调用处理
        
        Args:
            content: 当前轮次的对话内容
            
        Yields:
            流式响应的 chunks
        """
        print(f"DEBUG: stream_chat开始处理用户输入: {content}")  # 调试信息
        
        # 更新当前对话内容
        if self.current_conversation:
            self.current_conversation += f"\nUser: {content}\n"
        else:
            self.current_conversation = f"User: {content}\n"
            
        print(f"DEBUG: 当前对话内容:\n{self.current_conversation}")  # 调试信息
        
        while True:
            print(f"DEBUG: 当轮发送消息: {self.current_conversation}")
            # 获取可用工具列表
            tools = self.get_available_tools()
            mcp_tools = self._convert_mcp_tools_to_openai_format(tools)
            print(f"DEBUG: 可用工具数量: {len(tools)}")  # 调试信息
            
            # 合并用户传入的工具和 MCP 工具
            if 'tools' in kwargs:
                user_tools = kwargs.pop('tools')
                all_tools = mcp_tools + user_tools
            else:
                all_tools = mcp_tools
            
            print("DEBUG: 准备创建流式会话...")  # 调试信息
            print(all_tools)  # 调试信息
            try:
                # 使用上下文管理器创建流式会话（无状态模式）
                async with await self.client.responses.create(
                    model=self.model,
                    input=[{"role": "user", "content": self.current_conversation}],
                    tools=all_tools if all_tools else None,
                    store=False,  # 🔑 关键：不使用服务端状态管理，保持客户端管理
                    stream=True,
                    **kwargs
                ) as stream:
                    print("DEBUG: 流式会话创建成功")  # 调试信息
                    
                    # 处理流式响应
                    print("DEBUG: 开始处理流式响应...")  # 调试信息
                    final_message = None
                    async for chunk in stream:
                        chunk_data = chunk.model_dump()
                        
                        # 如果是最后一个完整的消息，保存下来
                        if chunk_data.get("type") == "response.completed":
                            final_message = chunk_data.get("response")
                            # 更新 usage 统计
                            if usage := final_message.get("usage"):
                                self.usage.input_tokens += usage.get("input_tokens", 0)
                                self.usage.output_tokens += usage.get("output_tokens", 0)
                        
                        # 将每个 chunk 返回给调用者
                        yield chunk_data
                    
                    # 在同一个上下文中处理工具调用
                    has_tool_calls = False
                    if final_message and final_message.get("output"):
                        for output in final_message["output"]:
                            print(f"DEBUG: 处理工具调用输出: {output}")  # 调试信息
                            result = await self._process_stream_tool_call(output)
                            if result:
                                has_tool_calls = True
                                # 添加工具调用结果到对话内容
                                self.current_conversation += f"Tool <{result.tool_name}> Result Returned: {result.tool_result}\n"
                    
                print("DEBUG: 流式响应处理完成")  # 调试信息
                
                # 如果没有工具调用，退出循环
                if not has_tool_calls:
                    print("DEBUG: 没有工具调用，流式对话结束")
                    break
                else:
                    print("DEBUG: 有工具调用，继续下一轮流式对话处理工具结果")
                    # 继续while循环，进行下一轮流式对话
                    
            except Exception as e:
                print(f"ERROR: 流式处理异常: {str(e)}")  # 错误信息
                raise
