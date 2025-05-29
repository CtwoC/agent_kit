import asyncio
from typing import List
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

mcp_url = "http://39.103.228.66:8165/mcp"
# local_mcp_url = "http://localhost:8165/mcp"
async def test_basic_features(client: Client):
    """测试基本功能：ping、列出工具、调用工具"""
    print("\n=== 测试基本功能 ===")
    await client.ping()
    print("ping success")

    # list tools
    tools = await client.list_tools()
    print(f"Available tools: {tools}")

    # call tool
    result = await client.call_tool("greet", {"name": "Alice"})
    print(f"Tool result: {result}")

async def test_resource_features(client: Client):
    """测试资源相关功能"""
    print("\n=== 测试资源功能 ===\n")
    try:
        # 列出所有资源
        resources = await client.list_resources()
        print(f"Available resources: {resources}")
        
        # 列出资源模板
        templates = await client.list_resource_templates()
        print(f"\nResource templates: {templates}")
        
        # 读取特定资源
        try:
            contents = await client.read_resource("greeting://Bob")
            print(f"\nResource contents: {contents}")
        except Exception as e:
            print(f"Read specific resource error: {e}")
            
    except Exception as e:
        print(f"Resource test error: {e}")

async def test_batch_operations(client: Client):
    """测试批量操作功能"""
    print("\n=== 测试批量操作 ===")
    try:
        # 并行执行多个工具调用
        batch_results = await asyncio.gather(
            client.call_tool("add", {"a": 1, "b": 2}),
            client.call_tool("add", {"a": 3, "b": 4}),
            client.call_tool("greet", {"name": "Charlie"})
        )
        print(f"Batch operations results: {batch_results}")
    except Exception as e:
        print(f"Batch operations error: {e}")

async def test_error_handling(client: Client):
    """测试错误处理功能"""
    print("\n=== 测试错误处理 ===")
    try:
        # 测试不存在的工具
        await client.call_tool("non_existent_tool", {})
    except Exception as e:
        print(f"Expected error caught: {e}")
    
    try:
        # 测试参数错误
        await client.call_tool("add", {"a": "not_a_number", "b": 2})
    except Exception as e:
        print(f"Parameter validation error caught: {e}")

async def test_connection_stability(client: Client):
    """测试连接稳定性"""
    print("\n=== 测试连接稳定性 ===")
    try:
        for i in range(3):
            await client.ping()
            await asyncio.sleep(1)
            print(f"Connection stable: ping {i+1}")
    except Exception as e:
        print(f"Connection stability test error: {e}")

async def test_prompts(client: Client):
    """测试prompts相关功能"""
    print("\n=== 测试Prompts功能 ===\n")
    try:
        # 列出所有可用的prompts
        prompts = await client.list_prompts()
        print(f"Available prompts: {prompts}")
        
        # 获取特定prompt
        try:
            prompt_result = await client.get_prompt("test_prompt", {"key": "value"})
            print(f"\nPrompt result: {prompt_result}")
        except Exception as e:
            print(f"Get specific prompt error: {e}")
            
    except Exception as e:
        print(f"Prompts test error: {e}")

async def main():
    transport = StreamableHttpTransport(mcp_url)
    async with Client(transport) as client:
        # 运行所有测试
        await test_basic_features(client)
        await test_resource_features(client)
        await test_batch_operations(client)
        await test_error_handling(client)
        await test_connection_stability(client)
        await test_prompts(client)

if __name__ == "__main__":
    asyncio.run(main())
