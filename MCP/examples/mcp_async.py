 # server_async.py
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP(name="Demo", port=8165, host="0.0.0.0")


# Add an addition tool
@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
async def greet(name: str) -> str:
    """Returns a simple greeting."""
    return f"Hello, {name}!"


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
async def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

mcp.run("streamable-http")