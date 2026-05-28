"""Minimal, modern MCP server entrypoint for this workspace.

Run locally with one of:
    python server.py
    uv run mcp dev server.py

Optional environment variables:
    MCP_SERVER_NAME=Custom Name
    MCP_TRANSPORT=stdio | streamable-http
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP


WORKSPACE_ROOT = Path(__file__).resolve().parent
SERVER_NAME = os.getenv("MCP_SERVER_NAME", "Workspace MCP Server")
TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()

mcp = FastMCP(
    SERVER_NAME,
    instructions=(
        "A general-purpose MCP server for basic workspace inspection, "
        "file reading, and small utility tasks."
    ),
    json_response=True,
    stateless_http=TRANSPORT == "streamable-http",
)


@mcp.tool()
def echo(text: str) -> str:
    """Return the provided text unchanged."""
    return text


@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def list_workspace_files(subdirectory: str = ".") -> list[str]:
    """List files and folders inside a workspace subdirectory."""
    base_path = _resolve_workspace_path(subdirectory)
    entries = sorted(base_path.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
    return [
        f"{entry.relative_to(WORKSPACE_ROOT)}{'/' if entry.is_dir() else ''}"
        for entry in entries
    ]


@mcp.tool()
def read_text_file(path: str) -> str:
    """Read a UTF-8 text file from the workspace."""
    file_path = _resolve_workspace_path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Not a file: {file_path}")
    return file_path.read_text(encoding="utf-8")


@mcp.tool()
def read_json_file(path: str) -> dict | list:
    """Read and parse a JSON file from the workspace."""
    file_path = _resolve_workspace_path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Not a file: {file_path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


@mcp.resource("workspace://server-info")
def server_info() -> str:
    """Expose a small summary of the running MCP server."""
    payload = {
        "name": SERVER_NAME,
        "transport": TRANSPORT,
        "workspace_root": str(WORKSPACE_ROOT),
        "available_tools": [
            "echo",
            "add_numbers",
            "list_workspace_files",
            "read_text_file",
            "read_json_file",
        ],
    }
    return json.dumps(payload, indent=2)


def _resolve_workspace_path(relative_path: str) -> Path:
    """Keep file access scoped to the workspace directory."""
    candidate = (WORKSPACE_ROOT / relative_path).resolve()
    if WORKSPACE_ROOT not in candidate.parents and candidate != WORKSPACE_ROOT:
        raise ValueError("Path must stay inside the workspace")
    return candidate


def main() -> None:
    """Run the MCP server with the requested transport."""
    if TRANSPORT == "streamable-http":
        mcp.run(transport="streamable-http")
        return

    if TRANSPORT != "stdio":
        raise ValueError(
            "Unsupported MCP_TRANSPORT. Use 'stdio' or 'streamable-http'."
        )

    mcp.run()


if __name__ == "__main__":
    main()
