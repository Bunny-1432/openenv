"""
Email Triage Environment Client.

Extends MCPToolClient and provides a ready-to-use client
for connecting to the Email Triage Environment server.

Example (local server):
    >>> from client import EmailTriageEnv
    >>> with EmailTriageEnv(base_url="http://localhost:8000").sync() as env:
    ...     env.reset()
    ...     tools = env.list_tools()
    ...     result = env.call_tool("get_email", email_id="e001")
    ...     result = env.call_tool("classify_email", email_id="e001", category="urgent")
    ...     print(result)

Example (HuggingFace Space):
    >>> env = EmailTriageEnv(base_url="https://<your-space>.hf.space")
    >>> with env.sync() as e:
    ...     e.reset()
    ...     e.call_tool("list_emails")

Example (Docker):
    >>> import asyncio
    >>> env = EmailTriageEnv.from_docker_image("email-triage-env:latest")
"""

from openenv.core.mcp_client import MCPToolClient


class EmailTriageEnv(MCPToolClient):
    """
    Client for the Email Triage Environment.

    Inherits all functionality from MCPToolClient:
      - list_tools()             : discover available MCP tools
      - call_tool(name, **kwargs): execute a tool by name
      - reset(**kwargs)          : start a new episode
      - step(action)             : low-level step (advanced use)
    """

    pass  # MCPToolClient provides all needed functionality
