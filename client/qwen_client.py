"""Qwen API 客户端"""
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

class QwenClient(BaseLLMClient):
    """Qwen API 客户端
    
    专门针对通义千问 API 的客户端实现。
    - 非流式对话与 OpenAI client 完全相同
    - 流式对话使用标准的 Chat Completions API (stream=True)
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-plus",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        **kwargs
    ):
        # 将 LLM 相关参数从 kwargs 中分离出来
        mcp_kwargs = {}
        if 'mcp_urls' in kwargs:
            mcp_kwargs['mcp_urls'] = kwargs.pop('mcp_urls')
        if 'enable_timeout_retry' in kwargs:
            mcp_kwargs['enable_timeout_retry'] = kwargs.pop('enable_timeout_retry')
            
        super().__init__(api_key, **mcp_kwargs)
        
        # 初始化 Qwen 客户端（使用 AsyncOpenAI 兼容接口）
        self.model = model
        self.base_url = base_url
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            **kwargs  # 直接透传其他参数给 SDK
        )

        # 对话状态
        self.current_conversation = ""  
        self.tool_results: List[ToolResult] = []
        
        # 初始化 usage 统计
        self.usage = Usage(
            input_price=ModelPrices.GPT41_INPUT_PRICE,  # 暂时使用相同价格，可以后续调整
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

    async def _process_chat_tool_call(self, tool_call: Dict[str, Any]) -> Optional[ToolResult]:
        """处理非流式对话中的工具调用
        
        Args:
            tool_call: 工具调用信息，格式为 chat completions API 的格式
            
        Returns:
            工具调用结果
        """
        tool_name = tool_call["function"]["name"]
        
        # 只处理 MCP 工具
        if not self.get_tool_by_name(tool_name):
            print(f"DEBUG: 跳过非 MCP 工具: {tool_name}")  # 调试信息
            return None
            
        tool_input = json.loads(tool_call["function"]["arguments"])
        return await self._call_tool(tool_name, tool_input)
    
    async def _process_stream_tool_call(self, tool_call: Dict[str, Any]) -> Optional[ToolResult]:
        """处理流式响应中的工具调用
        
        Args:
            tool_call: 工具调用信息，格式为 chat completions API 的格式
            
        Returns:
            工具调用结果
        """
        tool_name = tool_call["function"]["name"]
        
        # 只处理 MCP 工具
        if not self.get_tool_by_name(tool_name):
            print(f"DEBUG: 跳过非 MCP 工具: {tool_name}")  # 调试信息
            return None
            
        tool_input = json.loads(tool_call["function"]["arguments"])
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

    def _format_assistant_content(self, content: List[Dict[str, Any]]) -> str:
        """格式化助手的回复内容
        
        Args:
            content: 助手的回复内容列表
            
        Returns:
            格式化后的内容
        """
        formatted_content = ""
        for item in content:
            if item["role"] == "assistant":
                if item.get("content"):
                    formatted_content += item["content"]
                elif item.get("tool_calls"):
                    # OpenAI 的工具调用不会返回对话内容
                    pass
        return formatted_content

    def _generate_json_format_prompt(self, schema: Dict[str, Any]) -> str:
        """根据JSON schema生成格式要求的prompt
        
        Args:
            schema: JSON schema定义
            
        Returns:
            格式要求的prompt文本
        """
        if not schema or schema.get("type") != "json_schema":
            return ""
        
        json_schema = schema.get("json_schema", {})
        schema_def = json_schema.get("schema", {})
        
        # 生成示例JSON结构
        def generate_example_json(schema_obj: Dict[str, Any], depth: int = 0) -> str:
            if depth > 3:  # 防止无限递归
                return '"..."'
            
            schema_type = schema_obj.get("type", "string")
            properties = schema_obj.get("properties", {})
            required = schema_obj.get("required", [])
            
            if schema_type == "object" and properties:
                lines = ["{"]
                for i, (key, prop_schema) in enumerate(properties.items()):
                    indent = "  " * (depth + 1)
                    value = generate_example_json(prop_schema, depth + 1)
                    comma = "," if i < len(properties) - 1 else ""
                    lines.append(f'{indent}"{key}": {value}{comma}')
                lines.append("  " * depth + "}")
                return "\n".join(lines)
            
            elif schema_type == "array":
                items_schema = schema_obj.get("items", {"type": "string"})
                item_example = generate_example_json(items_schema, depth + 1)
                return f"[\n{'  ' * (depth + 1)}{item_example}\n{'  ' * depth}]"
            
            elif schema_type == "string":
                description = schema_obj.get("description", "字符串值")
                return f'"{description}"'
            
            elif schema_type == "number" or schema_type == "integer":
                return "0"
            
            elif schema_type == "boolean":
                return "true"
            
            else:
                return '"值"'
        
        try:
            example_json = generate_example_json(schema_def)
            
            # 提取所有必需字段
            def extract_required_fields(obj: Dict[str, Any], path: str = "") -> List[str]:
                fields = []
                if obj.get("type") == "object":
                    properties = obj.get("properties", {})
                    required = obj.get("required", [])
                    for field in required:
                        field_path = f"{path}.{field}" if path else field
                        fields.append(field_path)
                        # 递归处理嵌套对象
                        if field in properties:
                            nested_fields = extract_required_fields(properties[field], field_path)
                            fields.extend(nested_fields)
                return fields
            
            required_fields = extract_required_fields(schema_def)
            
            format_prompt = f"""\n\n请严格按照以下JSON格式返回结果：
{example_json}

⚠️ 重要提示：
1. 必须严格使用上述JSON中的字段名，不得更改或替换
2. 必须包含以下所有必需字段：{', '.join(required_fields)}
3. 字段名必须完全一致，包括大小写
4. 请勿添加schema中未定义的额外字段
5. 确保返回的是有效的JSON格式"""
            
            return format_prompt
        except Exception as e:
            print(f"DEBUG: 生成JSON格式prompt时出错: {e}")
            # 回退到简单提示
            return "\n\n请以JSON格式返回结果。"

    def _enhance_content_with_json_format(self, content: str, **kwargs) -> str:
        """增强content，如果有response_format则自动添加JSON格式要求
        
        Args:
            content: 原始content
            **kwargs: 可能包含response_format的参数
            
        Returns:
            增强后的content
        """
        response_format = kwargs.get("response_format")
        if not response_format:
            return content
        
        # 检查content中是否已经包含"json"或"JSON"
        needs_json_keyword = "json" not in content.lower()
        
        # 生成具体的格式要求
        format_prompt = self._generate_json_format_prompt(response_format)
        
        if needs_json_keyword:
            # 如果没有包含json字眼，先添加基本要求，再添加详细格式
            enhanced_content = content + "\n\n请以JSON格式返回结果。" + format_prompt
        else:
            # 如果已经包含json字眼，只添加详细格式要求
            enhanced_content = content + format_prompt
        
        print(f"DEBUG: 自动增强prompt，添加了JSON格式要求")
        return enhanced_content

    @async_retry(timeout=60.0)
    async def chat(self, content: str, **kwargs) -> Dict[str, Any]:
        """对话
        
        Args:
            content: 当前轮次的对话内容
            
        Returns:
            对话响应
        """
        print(f"DEBUG: chat开始处理用户输入: {content}")  # 调试信息
        
        # 🚀 自动增强prompt以支持结构化输出
        enhanced_content = self._enhance_content_with_json_format(content, **kwargs)
        if enhanced_content != content:
            print(f"DEBUG: prompt已自动增强以支持JSON格式输出")
        
        # 更新当前对话内容
        if self.current_conversation:
            self.current_conversation += f"\nUser: {enhanced_content}\n"
        else:
            self.current_conversation = f"User: {enhanced_content}\n"
        
        print(f"DEBUG: 当前对话内容:\n{self.current_conversation}")  # 调试信息
        
        # 循环处理，直到没有工具调用
        while True:
            # 获取可用工具列表
            tools = self.get_available_tools()
            chat_tools = self._convert_mcp_tools_to_chat_format(tools)
            print(f"DEBUG: 可用工具数量: {len(tools)}")  # 调试信息
            
            # 合并用户传入的工具和 MCP 工具
            if 'tools' in kwargs:
                user_tools = kwargs.pop('tools')
                all_tools = chat_tools + user_tools
            else:
                all_tools = chat_tools
            
            print(f"DEBUG: 准备调用chat completions API...")  # 调试信息
            
            # 调用chat completions API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": self.current_conversation}
                ],
                tools=all_tools if all_tools else None,  # 如果没有工具就不传tools参数
                **kwargs
            )
            
            response_data = response.model_dump()
            print(f"DEBUG: 收到API响应")  # 调试信息
            
            # 更新usage统计
            if usage := response_data.get("usage"):
                self.usage.input_tokens += usage.get("prompt_tokens", 0)
                self.usage.output_tokens += usage.get("completion_tokens", 0)
                print(f"DEBUG: 更新usage - 输入:{usage.get('prompt_tokens', 0)}, 输出:{usage.get('completion_tokens', 0)}")
            
            message = response_data["choices"][0]["message"]
            
            # 检查是否有工具调用
            has_tool_calls = False
            if message.get("tool_calls"):
                print(f"DEBUG: 发现{len(message['tool_calls'])}个工具调用")  # 调试信息
                
                # 添加助手消息到对话历史
                assistant_content = message.get("content", "")
                if assistant_content:
                    self.current_conversation += f"Assistant: {assistant_content}\n"
                
                # 处理每个工具调用
                for tool_call in message["tool_calls"]:
                    result = await self._process_chat_tool_call(tool_call)
                    if result:
                        has_tool_calls = True
                        # 添加工具调用结果到对话内容
                        tool_response = f"Tool <{result.tool_name}> returned: {result.tool_result}\n"
                        self.current_conversation += tool_response
                        print(f"DEBUG: 工具调用结果已添加到对话")
            else:
                # 没有工具调用，添加助手回复到对话历史
                assistant_content = message.get("content", "")
                if assistant_content:
                    self.current_conversation += f"Assistant: {assistant_content}\n"
                print(f"DEBUG: 没有工具调用，对话结束")
            
            # 如果没有工具调用，返回响应
            if not has_tool_calls:
                print(f"DEBUG: chat函数完成")
                return response_data
            else:
                print(f"DEBUG: 继续下一轮对话处理工具调用结果")
                # 继续循环处理工具调用结果

    def _convert_chat_chunk_to_response_format(self, chunk_data: Dict[str, Any], chunk_index: int = 0) -> Dict[str, Any]:
        """将Chat Completions API的chunk转换为类似Responses API的格式
        
        Args:
            chunk_data: Chat API的原始chunk数据
            chunk_index: chunk索引
            
        Returns:
            转换后的响应格式
        """
        if not chunk_data.get("choices"):
            # 如果没有choices，返回原始数据
            return chunk_data
        
        choice = chunk_data["choices"][0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")
        
        # 根据内容类型生成不同的响应格式
        if delta.get("content"):
            # 文本内容增量
            return {
                "type": "response.function_call_arguments.delta",
                "delta": delta["content"]
            }
        
        elif delta.get("tool_calls"):
            # 工具调用增量处理
            tool_call = delta["tool_calls"][0]  # 通常只有一个工具调用
            
            # 检查是否是工具调用开始（有工具ID和名称）
            if tool_call.get("id") and tool_call.get("function", {}).get("name"):
                return {
                    "type": "response.tool_call_start",
                    "tool_call_id": tool_call["id"],
                    "tool_name": tool_call["function"]["name"]
                }
            # 检查是否有参数增量
            elif tool_call.get("function", {}).get("arguments"):
                return {
                    "type": "response.function_call_arguments.delta",
                    "delta": tool_call["function"]["arguments"]
                }
            else:
                # 其他工具调用相关的增量
                return {
                    "type": "response.function_call_arguments.delta",
                    "delta": ""
                }
        
        elif finish_reason == "tool_calls":
            # 工具调用完成
            return {
                "type": "response.function_call_arguments.done"
            }
        
        elif finish_reason:
            # 普通响应完成
            return {
                "type": "response.completed",
                "response": {
                    "output": [{
                        "type": "message",
                        "status": "completed",
                        "content": [{"type": "text", "text": ""}]  # 这里可以根据需要填充
                    }],
                    "usage": chunk_data.get("usage")
                }
            }
        
        elif chunk_index == 0:
            # 第一个chunk，表示响应开始
            return {
                "type": "response.created"
            }
        
        else:
            # 其他情况，返回进行中状态
            return {
                "type": "response.in_progress"
            }

    @stream_async_retry(max_retries=3, chunk_timeout=60.0)
    async def stream_chat(self, content: str, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """流式对话和工具调用处理
        
        注意：流式接口通常不提供准确的token统计信息，因此usage.input_tokens和usage.output_tokens
        在使用流式模式时将无法正确统计。如需准确的token统计，请使用非流式的chat()方法。
        
        Args:
            content: 当前轮次的对话内容
            
        Yields:
            流式响应的 chunks（转换为类似OpenAI Responses API的格式）
        """
        print(f"DEBUG: stream_chat开始处理用户输入: {content}")  # 调试信息
        
        # 🚀 自动增强prompt以支持结构化输出
        enhanced_content = self._enhance_content_with_json_format(content, **kwargs)
        if enhanced_content != content:
            print(f"DEBUG: prompt已自动增强以支持JSON格式输出")
        
        # 更新当前对话内容
        if self.current_conversation:
            self.current_conversation += f"\nUser: {enhanced_content}\n"
        else:
            self.current_conversation = f"User: {enhanced_content}\n"
            
        print(f"DEBUG: 当前对话内容:\n{self.current_conversation}")  # 调试信息
        
        while True:
            print(f"DEBUG: 当轮发送消息: {self.current_conversation}")
            # 获取可用工具列表
            tools = self.get_available_tools()
            chat_tools = self._convert_mcp_tools_to_chat_format(tools)
            print(f"DEBUG: 可用工具数量: {len(tools)}")  # 调试信息
            
            # 合并用户传入的工具和 MCP 工具
            if 'tools' in kwargs:
                user_tools = kwargs.pop('tools')
                all_tools = chat_tools + user_tools
            else:
                all_tools = chat_tools
            
            print("DEBUG: 准备创建流式会话...")  # 调试信息
            
            # 存储工具调用信息
            accumulated_tool_calls = {}
            collected_content = ""
            final_response = None
            chunk_index = 0
            
            try:
                # 使用 Chat Completions API 的流式模式
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": self.current_conversation}],
                    tools=all_tools if all_tools else None,
                    stream=True,
                    **kwargs
                )
                
                print("DEBUG: 流式会话创建成功")  # 调试信息
                
                # 处理流式响应
                print("DEBUG: 开始处理流式响应...")  # 调试信息
                async for chunk in stream:
                    chunk_data = chunk.model_dump()
                    
                    # 🚀 转换为标准化格式并返回给调用者
                    standardized_chunk = self._convert_chat_chunk_to_response_format(chunk_data, chunk_index)
                    yield standardized_chunk
                    chunk_index += 1
                    
                    # 收集完整响应数据
                    if chunk_data.get("choices"):
                        choice = chunk_data["choices"][0]
                        delta = choice.get("delta", {})
                        
                        # 收集内容
                        if delta.get("content"):
                            collected_content += delta["content"]
                        
                        # 收集工具调用
                        if delta.get("tool_calls"):
                            for tool_call in delta["tool_calls"]:
                                tool_id = tool_call.get("id")
                                if tool_id:
                                    # 初始化工具调用记录
                                    if tool_id not in accumulated_tool_calls:
                                        accumulated_tool_calls[tool_id] = {
                                            "id": tool_id,
                                            "type": tool_call.get("type", "function"),
                                            "function": {
                                                "name": "",
                                                "arguments": ""
                                            }
                                        }
                                    
                                    # 累积工具调用信息
                                    if tool_call.get("function"):
                                        func = tool_call["function"]
                                        if func.get("name"):
                                            accumulated_tool_calls[tool_id]["function"]["name"] = func["name"]
                                        if func.get("arguments"):
                                            accumulated_tool_calls[tool_id]["function"]["arguments"] += func["arguments"]
                                else:
                                    # 处理没有ID的情况（使用index作为临时ID）
                                    tool_index = tool_call.get("index", 0)
                                    temp_id = f"temp_{tool_index}"
                                    
                                    if temp_id not in accumulated_tool_calls:
                                        accumulated_tool_calls[temp_id] = {
                                            "id": temp_id,
                                            "type": tool_call.get("type", "function"),
                                            "function": {
                                                "name": "",
                                                "arguments": ""
                                            }
                                        }
                                    
                                    if tool_call.get("function"):
                                        func = tool_call["function"]
                                        if func.get("name"):
                                            accumulated_tool_calls[temp_id]["function"]["name"] = func["name"]
                                        if func.get("arguments"):
                                            accumulated_tool_calls[temp_id]["function"]["arguments"] += func["arguments"]
                        
                        # 检查是否是最后一个chunk
                        if choice.get("finish_reason"):
                            final_response = {
                                "choices": [{
                                    "message": {
                                        "role": "assistant",
                                        "content": collected_content,
                                        "tool_calls": list(accumulated_tool_calls.values()) if accumulated_tool_calls else None
                                    },
                                    "finish_reason": choice["finish_reason"]
                                }],
                                "usage": chunk_data.get("usage")
                            }
                    
                    # 注意：流式接口通常不提供准确的token统计信息
                    # 因此在流式模式下不进行token统计
                    # if chunk_data.get("usage"):
                    #     usage = chunk_data["usage"]
                    #     self.usage.input_tokens += usage.get("prompt_tokens", 0)
                    #     self.usage.output_tokens += usage.get("completion_tokens", 0)
                
                print("DEBUG: 流式响应处理完成")  # 调试信息
                
                # 处理工具调用
                has_tool_calls = False
                if final_response and accumulated_tool_calls:
                    print(f"DEBUG: 发现{len(accumulated_tool_calls)}个工具调用")
                    
                    # 添加助手消息到对话历史
                    if collected_content:
                        self.current_conversation += f"Assistant: {collected_content}\n"
                    
                    # 处理每个工具调用
                    for tool_call in accumulated_tool_calls.values():
                        result = await self._process_stream_tool_call(tool_call)
                        if result:
                            has_tool_calls = True
                            # 添加工具调用结果到对话内容
                            self.current_conversation += f"Tool <{result.tool_name}> Result Returned: {result.tool_result}\n"
                else:
                    # 没有工具调用，添加助手回复到对话历史
                    if collected_content:
                        self.current_conversation += f"Assistant: {collected_content}\n"
                
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