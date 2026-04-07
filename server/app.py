"""
FastAPI application for the Email Triage Environment.

Usage:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
    # or via entry point:
    uv run --project . server
"""

from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

from server.email_environment import EmailTriageEnvironment

# Pass the class (factory) so each WebSocket session gets its own instance.
# Use MCP types — all environment interactions happen through MCP tool calls.
app = create_app(
    EmailTriageEnvironment,
    CallToolAction,
    CallToolObservation,
    env_name="email_triage_env",
)


def main() -> None:
    """Entry point: uv run --project . server"""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
