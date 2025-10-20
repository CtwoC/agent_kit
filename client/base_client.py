"""LLM 客户端基类"""
import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Dict, Any, List, Union
from fastmcp import Client as MCPClient
from fastmcp.client.transports import StreamableHttpTransport
from exceptions import StreamTimeoutError
from utils.retry import async_retry, mcp_tool_retry

@dataclass
class Usage:
    """Token 使用和成本统计"""
    # token 统计
    input_tokens: int = 0
    output_tokens: int = 0
    
    # 价格 (每百万 token 的美元价格)
    input_price: float = 0.0
    output_price: float = 0.0
    
    @property
    def input_cost(self) -> float:
        """Input token 成本"""
        return self.input_tokens * self.input_price / 1_000_000
    
    @property
    def output_cost(self) -> float:
        """Output token 成本"""
        return self.output_tokens * self.output_price / 1_000_000
    
    @property
    def total_tokens(self) -> int:
        """Token 总数"""
        return self.input_tokens + self.output_tokens
    
    @property
    def total_cost(self) -> float:
        """Token 总成本"""
        return self.input_cost + self.output_cost
    
    def reset(self):
        """Reset usage statistics"""
        self.input_tokens = 0
        self.output_tokens = 0

# 各模型的价格常量
class ModelPrices:
    # OpenAI GPT-4.1
    GPT41_INPUT_PRICE = 2.0   # $2.00 / 1M tokens
    GPT41_OUTPUT_PRICE = 8.0   # $8.00 / 1M tokens
    
    # Claude-3 Sonnet
    CLAUDE35_INPUT_PRICE = 3.0   # $3.00 / 1M tokens
    CLAUDE35_OUTPUT_PRICE = 15.0  # $15.00 / 1M tokens

@dataclass
class Tool:
    """MCP 工具信息"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    url: str  # 工具所属的 MCP URL

class BaseLLMClient:
    """LLM 客户端基类"""
    
    # 默认的 chunk 超时时间（秒）
    DEFAULT_CHUNK_TIMEOUT = 10.0
    
    def __init__(
        self,
        api_key: str,
        mcp_urls: Optional[Union[str, List[str]]] = None,  # MCP 服务器 URL列表
        enable_timeout_retry: bool = True,  # 是否启用超时重试
        **kwargs
    ):
        self.api_key = api_key
        self.enable_timeout_retry = enable_timeout_retry
        self.kwargs = kwargs
        
        # MCP 相关
        self.mcp_urls = [mcp_urls] if isinstance(mcp_urls, str) else mcp_urls or []
        self.mcp_tools: Dict[str, Tool] = {}  # 以工具名为 key 的工具字典
        self.mcp_transports: Dict[str, StreamableHttpTransport] = {}
        
        # 初始化usage统计（子类应该重新设置价格）
        self.usage = Usage()
        
    @mcp_tool_retry(max_retries=3, timeout=30.0, backoff_delay=2.0)
    async def _init_mcp_connection(self, url: str):
        """初始化单个 MCP 连接并获取工具列表
        
        Args:
            url: MCP 服务器 URL
        """
        print(f"DEBUG: 开始初始化MCP连接 - {url}")
        
        # 创建 transport
        transport = StreamableHttpTransport(url)
        self.mcp_transports[url] = transport
        
        # 创建客户端并测试连接
        async with MCPClient(transport) as client:
            print(f"DEBUG: 正在ping MCP服务器 - {url}")
            await client.ping()
            print(f"DEBUG: MCP服务器ping成功 - {url}")
            
            # 获取工具列表
            print(f"DEBUG: 正在获取工具列表 - {url}")
            tools = await client.list_tools()
            print(f"DEBUG: 获取到{len(tools)}个工具 - {url}")
            
            # 将工具信息添加到字典
            for tool in tools:
                self.mcp_tools[tool.name] = Tool(
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.inputSchema,
                    url=url
                )
                
        print(f"DEBUG: MCP连接初始化完成 - {url}")

    async def __aenter__(self):
        """初始化 MCP 连接"""
        # 初始化所有 MCP 客户端
        for url in self.mcp_urls:
            try:
                await self._init_mcp_connection(url)
            except Exception as e:
                print(f"ERROR: MCP连接初始化最终失败 - {url}")
                print(f"  最终异常: {type(e).__name__}: {str(e)}")
                # 继续处理其他URL，不让一个失败影响全部
                continue
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """关闭 MCP 连接"""
        # StreamableHttpTransport 使用了 asynccontextmanager，会自动处理资源清理
        pass
    
    async def reset(self):
        """重置客户端状态用于连接池复用"""
        # 重置对话状态（如果存在）
        if hasattr(self, 'current_conversation'):
            self.current_conversation = ""
        if hasattr(self, 'tool_results'):
            self.tool_results.clear()
        if hasattr(self, 'thinking_process'):
            self.thinking_process.clear()
            
        # 重置使用统计
        self.usage.reset()
        
        # 注意：不重置 mcp_tools 和 mcp_transports，因为它们是连接级别的资源
        # 如果需要重置 MCP 连接，应该使用 close() 然后重新初始化
    
    async def close(self):
        """显式关闭连接和清理资源"""
        # 清理 MCP 传输连接
        self.mcp_transports.clear()
        self.mcp_tools.clear()
        
        # 重置使用统计
        self.usage.reset()
                
    def get_available_tools(self) -> List[Tool]:
        """获取所有可用的工具列表"""
        return list(self.mcp_tools.values())
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Tool]:
        """根据工具名称获取工具信息"""
        return self.mcp_tools.get(tool_name)
    
    @mcp_tool_retry(max_retries=3, timeout=15.0, backoff_delay=1.0)
    async def call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            工具调用结果
            
        Raises:
            ValueError: 如果工具不存在
        """
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
            
        if tool.url not in self.mcp_transports:
            raise ValueError(f"MCP connection for {tool.url} not initialized")
            
        print(f"DEBUG: MCP工具调用开始 - {tool_name}, URL: {tool.url}")
        
        # 每次调用都创建新的客户端
        transport = self.mcp_transports[tool.url]
        try:
            async with MCPClient(transport) as client:
                result = await client.call_tool(tool_name, params)
                print(f"DEBUG: MCP工具调用成功 - {tool_name}")
                return result
        except Exception as e:
            print(f"ERROR: MCP工具调用失败 - {tool_name}")
            print(f"  错误类型: {type(e).__name__}")
            print(f"  错误信息: {str(e)}")
            # 重新抛出异常，让重试机制处理
            raise e

    async def _handle_stream(self, stream: AsyncIterator) -> AsyncIterator:
        """处理流式响应
        
        Args:
            stream: 原始的流式响应迭代器
            
        Yields:
            处理过的流式响应
            
        Raises:
            StreamTimeoutError: 当启用超时重试且超过指定时间没有收到新的 chunk
        """
        try:
            while True:
                try:
                    if self.enable_timeout_retry:
                        chunk = await asyncio.wait_for(
                            anext(stream),
                            timeout=self.DEFAULT_CHUNK_TIMEOUT
                        )
                    else:
                        chunk = await anext(stream)
                    yield chunk
                except asyncio.TimeoutError:
                    raise StreamTimeoutError(
                        f"No response received for {self.DEFAULT_CHUNK_TIMEOUT} seconds"
                    )
                except StopAsyncIteration:
                    break
        except Exception as e:
            # 其他异常直接往上抛
            raise e

    @async_retry()
    async def chat(self, content: str, **kwargs) -> Dict[str, Any]:
        """非流式对话
        
        Args:
            content: 对话内容
            **kwargs: 其他参数
            
        Returns:
            API 响应
        """
        raise NotImplementedError()

    @async_retry()
    async def stream_chat(self, content: str, **kwargs) -> AsyncIterator:
        """流式对话
        
        Args:
            content: 对话内容
            **kwargs: 其他参数
            
        Yields:
            流式响应的 chunks
        """
        raise NotImplementedError()
