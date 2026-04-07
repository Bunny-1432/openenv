"""
FastAPI application for the Email Triage Environment.

Usage:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
    # or via entry point:
    uv run --project . server
"""

import json
from typing import Any, Dict, Literal, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation
from pydantic import model_validator

from server.email_environment import EmailTriageEnvironment


class FlexibleCallToolAction(CallToolAction):
    """
    Extends CallToolAction to accept `arguments` as either a dict OR a JSON
    string (as sent by the OpenEnv Playground UI).
    Also accepts type='tool_call' as an alias for 'call_tool'.
    """

    @model_validator(mode="before")
    @classmethod
    def coerce_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Coerce type alias
            if values.get("type") == "tool_call":
                values["type"] = "call_tool"
            # Coerce arguments string → dict
            args = values.get("arguments")
            if isinstance(args, str):
                try:
                    values["arguments"] = json.loads(args)
                except (json.JSONDecodeError, ValueError):
                    values["arguments"] = {}
            elif args is None:
                values["arguments"] = {}
        return values


# Pass the class (factory) so each WebSocket session gets its own instance.
# Use MCP types — all environment interactions happen through MCP tool calls.
app = create_app(
    EmailTriageEnvironment,
    FlexibleCallToolAction,
    CallToolObservation,
    env_name="email_triage_env",
)


def main() -> None:
    """Entry point: uv run --project . server"""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

