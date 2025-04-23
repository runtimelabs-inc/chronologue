# server-verifier.py
# This file is used to verify the server is working correctly

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# # Starting MCP inspector...
# ⚙️ Proxy server listening on port 6277
# 🔍 MCP Inspector is up and running at http://111.0.0.1:1111 🚀 (follow the link)
# Connect to the server 