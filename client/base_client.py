"""LLM 客户端基类"""
import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Dict, Any, List, Union
from fastmcp import Client as MCPClient
from fastmcp.client.transports import StreamableHttpTransport
from exceptions import StreamTimeoutError
from retry import async_retry

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
        llm_base_url: Optional[str] = None,  # LLM API 基础 URL
        mcp_urls: Optional[Union[str, List[str]]] = None,  # MCP 服务器 URL列表
        enable_timeout_retry: bool = True,  # 是否启用超时重试
        **kwargs
    ):
        self.api_key = api_key
        self.llm_base_url = llm_base_url
        self.enable_timeout_retry = enable_timeout_retry
        self.kwargs = kwargs
        
        # MCP 相关
        self.mcp_urls = [mcp_urls] if isinstance(mcp_urls, str) else mcp_urls or []
        self.mcp_tools: Dict[str, Tool] = {}  # 以工具名为 key 的工具字典
        self.mcp_transports: Dict[str, StreamableHttpTransport] = {}
        
    async def __aenter__(self):
        """初始化 MCP 连接"""
        # 初始化所有 MCP 客户端
        for url in self.mcp_urls:
            await self._init_mcp_connection(url)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """关闭 MCP 连接"""
        # 关闭所有 transport
        for transport in self.mcp_transports.values():
            await transport.aclose()
                
    async def _init_mcp_connection(self, url: str):
        """初始化单个 MCP 连接并获取工具列表
        
        Args:
            url: MCP 服务器 URL
        """
        try:
            # 创建 transport
            transport = StreamableHttpTransport(url)
            self.mcp_transports[url] = transport
            
            # 创建客户端并测试连接
            async with MCPClient(transport) as client:
                await client.ping()
                # 获取工具列表
                tools = await client.list_tools()
                
                # 将工具信息添加到字典
                for tool in tools:
                    self.mcp_tools[tool.name] = Tool(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.inputSchema,
                        url=url
                    )
                
        except Exception as e:
            print(f"Failed to initialize MCP connection for {url}: {e}")
            
    def get_available_tools(self) -> List[Tool]:
        """获取所有可用的工具列表"""
        return list(self.mcp_tools.values())
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Tool]:
        """根据工具名称获取工具信息"""
        return self.mcp_tools.get(tool_name)
    
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
            
        # 每次调用都创建新的客户端
        transport = self.mcp_transports[tool.url]
        async with MCPClient(transport) as client:
            return await client.call_tool(tool_name, params)

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

    @async_retry()
    async def tool_call(self, content: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """工具调用
        
        Args:
            content: 对话内容
            tools: 工具定义列表
            **kwargs: 其他参数
            
        Returns:
            API 响应
        """
        raise NotImplementedError()

    @async_retry()
    async def stream_tool_call(self, content: str, tools: List[Dict], **kwargs) -> AsyncIterator:
        """流式工具调用
        
        Args:
            content: 对话内容
            tools: 工具定义列表
            **kwargs: 其他参数
            
        Yields:
            流式响应的 chunks
        """
        raise NotImplementedError()
