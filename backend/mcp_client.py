"""MCP Client — connects to external MCP servers and makes their tools available to your agent."""

import json
import asyncio
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClientManager:
    """Manages connections to multiple MCP servers and exposes their tools."""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._tools: dict[str, dict] = {}  # tool_name → {session, schema}
        self._exit_stack = AsyncExitStack()
        self._initialized = False

    async def connect(self, servers: dict):
        """
        Connect to MCP servers.

        servers: dict of server_name → {command, args, env}
        Example:
            {
                "slack": {"command": "uvx", "args": ["slack-mcp-server"]},
                "github": {"command": "uvx", "args": ["github-mcp-server"]},
            }
        """
        for name, config in servers.items():
            try:
                server_params = StdioServerParameters(
                    command=config["command"],
                    args=config.get("args", []),
                    env=config.get("env"),
                )

                stdio_transport = await self._exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read_stream, write_stream = stdio_transport
                session = await self._exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()

                # Discover tools from this server
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    tool_name = f"{name}__{tool.name}"  # Prefix with server name to avoid collisions
                    self._tools[tool_name] = {
                        "session": session,
                        "original_name": tool.name,
                        "server": name,
                        "schema": {
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "description": f"[{name}] {tool.description}",
                                "parameters": tool.inputSchema if tool.inputSchema else {"type": "object", "properties": {}},
                            },
                        },
                    }

                self._sessions[name] = session
                print(f"[MCP] Connected to '{name}' — {len(tools_response.tools)} tools available")

            except Exception as e:
                print(f"[MCP] Failed to connect to '{name}': {e}")

        self._initialized = True

    def get_tool_schemas(self) -> list[dict]:
        """Get OpenAI-compatible tool schemas for all MCP tools."""
        return [tool["schema"] for tool in self._tools.values()]

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool by name and return the result as a string."""
        if tool_name not in self._tools:
            return f"Error: Unknown MCP tool '{tool_name}'"

        tool_info = self._tools[tool_name]
        session = tool_info["session"]
        original_name = tool_info["original_name"]

        try:
            result = await session.call_tool(original_name, arguments)
            # Extract text content from the result
            if result.content:
                return "\n".join(
                    block.text for block in result.content if hasattr(block, "text")
                )
            return "Tool returned no content."
        except Exception as e:
            return f"Error calling MCP tool '{tool_name}': {e}"

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Check if a tool name belongs to an MCP server."""
        return tool_name in self._tools

    async def close(self):
        """Close all MCP connections."""
        await self._exit_stack.aclose()


# --- Synchronous wrapper for use in the agent loop ---

_mcp_manager: MCPClientManager | None = None
_loop: asyncio.AbstractEventLoop | None = None


def init_mcp_client(servers: dict):
    """Initialize the MCP client with server configurations (call once at startup)."""
    global _mcp_manager, _loop

    if not servers:
        return

    _mcp_manager = MCPClientManager()
    _loop = asyncio.new_event_loop()
    _loop.run_until_complete(_mcp_manager.connect(servers))


def get_mcp_tool_schemas() -> list[dict]:
    """Get all MCP tool schemas (OpenAI format)."""
    if _mcp_manager is None:
        return []
    return _mcp_manager.get_tool_schemas()


def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool synchronously."""
    if _mcp_manager is None:
        return "MCP client not initialized."
    return _loop.run_until_complete(_mcp_manager.call_tool(tool_name, arguments))


def is_mcp_tool(tool_name: str) -> bool:
    """Check if a tool name is from an MCP server."""
    if _mcp_manager is None:
        return False
    return _mcp_manager.is_mcp_tool(tool_name)
