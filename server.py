"""
server.py

Production-friendly FastMCP + FastAPI server.

Includes:
- Root health endpoint: GET /
- Health endpoint: GET /health
- OpenAI-compatible metadata endpoints
- Modern FastMCP HTTP mounting
- Explicit streamable-http app transport
- Public MCP endpoint mounted at /mcp/

Run locally:
    uvicorn server:app --host 0.0.0.0 --port 8000

Render start command:
    uvicorn server:app --host 0.0.0.0 --port $PORT

OpenAI / MCP server URL:
    https://YOUR-DOMAIN.onrender.com/mcp/
"""

from __future__ import annotations

import os

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from pydantic import BaseModel, Field

import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

APP_NAME = os.getenv("APP_NAME", "Big Baby MCP Server")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "Remote MCP server exposed over Streamable HTTP.",
)

PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "https://your-render-service.onrender.com",
).rstrip("/")


# ---------------------------------------------------------------------
# OpenAI-compatible search/fetch schemas
# ---------------------------------------------------------------------
# OpenAI's MCP guidance for ChatGPT/deep research compatibility centers on
# exposing read-only `search` and `fetch` tools with predictable result shapes.
# Replace the implementation bodies below with your real GitHub/data logic.


class SearchResult(BaseModel):
    id: str = Field(..., description="Stable unique ID for this result.")
    title: str = Field(..., description="Human-readable result title.")
    url: str = Field(..., description="Canonical URL for citation.")
    text: str | None = Field(
        default=None,
        description="Short preview/snippet for the result.",
    )


class SearchOutput(BaseModel):
    results: list[SearchResult]


class FetchOutput(BaseModel):
    id: str
    title: str
    url: str
    text: str


# ---------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------

mcp = FastMCP(
    name=APP_NAME,
    instructions=(
        "This MCP server exposes tools over Streamable HTTP. "
        "Use search to find relevant items, then fetch to retrieve full content."
    ),
)


@mcp.tool(
    output_schema=SearchOutput.model_json_schema(),
    annotations={
        "title": "Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def search(query: str) -> dict[str, Any]:
    """
    Search for relevant documents/items.

    Args:
        query: The user's search query.

    Returns:
        A list of search results with id, title, url, and optional text.
    """

    # TODO: Replace this placeholder with your real GitHub/repo/search logic.
    # Keep the return shape stable for OpenAI MCP compatibility.
    return {
        "results": [
            {
                "id": "health",
                "title": "MCP server health endpoint",
                "url": f"{PUBLIC_BASE_URL}/health",
                "text": f"Server is running. Query received: {query}",
            }
        ]
    }


@mcp.tool(
    output_schema=FetchOutput.model_json_schema(),
    annotations={
        "title": "Fetch",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fetch(id: str) -> dict[str, Any]:
    """
    Fetch a document/item by ID.

    Args:
        id: The stable ID returned by search.

    Returns:
        Full item content with id, title, url, and text.
    """

    # TODO: Replace this placeholder with your real fetch logic.
    return {
        "id": id,
        "title": f"Fetched item: {id}",
        "url": f"{PUBLIC_BASE_URL}/",
        "text": (
            f"This is placeholder content for item '{id}'. "
            "Replace the fetch() body in server.py with your real data retrieval."
        ),
    }
    


def get_drive_service():
    raw_credentials = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not raw_credentials:
        raise RuntimeError(
            "Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable."
        )

    service_account_info = json.loads(raw_credentials)

    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=DRIVE_SCOPES,
    )

    return build("drive", "v3", credentials=credentials)


class MoveFileOutput(BaseModel):
    ok: bool
    file_id: str
    destination_folder_id: str
    message: str


@mcp.tool(
    name="move_file",
    output_schema=MoveFileOutput.model_json_schema(),
    description=(
        "Use this when the user explicitly asks to move, organize, file, relocate, "
        "or place one document/file into a specific destination folder. "
        "Do not use this to search for files, read file contents, rename files, "
        "delete files, create folders, or move multiple files unless the user has "
        "clearly provided the exact file_id and destination_folder_id for this call. "
        "This action changes the file's folder location and should require user approval."
    ),
    annotations={
    "title": "Move File",
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": True,
},
)
async def move_file(file_id: str, destination_folder_id: str) -> dict[str, Any]:
    """
    Move one Google Drive file/document into one destination folder.

    Args:
        file_id: The exact Google Drive file ID to move.
        destination_folder_id: The exact Google Drive folder ID to move the file into.

    Returns:
        Confirmation that the file was moved, or an error message.
    """

    try:
        drive_service = get_drive_service()

        file_metadata = drive_service.files().get(
            fileId=file_id,
            fields="id, name, parents, webViewLink",
            supportsAllDrives=True,
        ).execute()

        previous_parents = ",".join(file_metadata.get("parents", []))

        moved_file = drive_service.files().update(
            fileId=file_id,
            addParents=destination_folder_id,
            removeParents=previous_parents,
            fields="id, name, parents, webViewLink",
            supportsAllDrives=True,
        ).execute()

        return {
            "ok": True,
            "file_id": moved_file["id"],
            "destination_folder_id": destination_folder_id,
            "message": (
                f"Moved '{moved_file.get('name', file_id)}' "
                f"to folder {destination_folder_id}."
            ),
        }

    except HttpError as error:
        return {
            "ok": False,
            "file_id": file_id,
            "destination_folder_id": destination_folder_id,
            "message": f"Google Drive API error: {error}",
        }

    except Exception as error:
        return {
            "ok": False,
            "file_id": file_id,
            "destination_folder_id": destination_folder_id,
            "message": f"Move failed: {error}",
        }
# ---------------------------------------------------------------------
# FastMCP ASGI app, mounted with explicit streamable-http transport
# ---------------------------------------------------------------------

mcp_app = mcp.http_app(
    path="/",
    transport="streamable-http",
    stateless_http=True,
)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=mcp_app.router.lifespan_context,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    
)


# ---------------------------------------------------------------------
# Health + metadata endpoints
# ---------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    """
    Root health endpoint.

    Useful for Render, uptime checks, and quick browser verification.
    """
    return {
        "ok": True,
        "name": APP_NAME,
        "version": APP_VERSION,
        "transport": "streamable-http",
        "mcp_url": f"{PUBLIC_BASE_URL}/mcp/",
        "health_url": f"{PUBLIC_BASE_URL}/health",
    }


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "healthy",
        "name": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/metadata", include_in_schema=False)
async def metadata() -> dict[str, Any]:
    """
    Simple machine-readable metadata endpoint.
    """
    return {
        "name": APP_NAME,
        "description": APP_DESCRIPTION,
        "version": APP_VERSION,
        "mcp": {
            "transport": "streamable-http",
            "url": f"{PUBLIC_BASE_URL}/mcp/",
        },
        "endpoints": {
            "root": f"{PUBLIC_BASE_URL}/",
            "health": f"{PUBLIC_BASE_URL}/health",
            "openapi": f"{PUBLIC_BASE_URL}/openapi.json",
            "plugin_manifest": f"{PUBLIC_BASE_URL}/.well-known/ai-plugin.json",
        },
    }


@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def ai_plugin_manifest() -> JSONResponse:
    """
    OpenAI/ChatGPT-style metadata manifest.

    This is mainly for compatibility/discovery. The actual MCP endpoint is /mcp/.
    """
    manifest = {
        "schema_version": "v1",
        "name_for_human": APP_NAME,
        "name_for_model": (
            APP_NAME.lower()
            .replace(" ", "_")
            .replace("-", "_")
        ),
        "description_for_human": APP_DESCRIPTION,
        "description_for_model": (
            "Remote MCP server. Use the MCP endpoint for tool discovery and calls."
        ),
        "auth": {
            "type": "none",
        },
        "api": {
            "type": "openapi",
            "url": f"{PUBLIC_BASE_URL}/openapi.json",
            "is_user_authenticated": False,
        },
        "logo_url": f"{PUBLIC_BASE_URL}/logo.png",
        "contact_email": os.getenv("CONTACT_EMAIL", "support@example.com"),
        "legal_info_url": os.getenv(
            "LEGAL_INFO_URL",
            f"{PUBLIC_BASE_URL}/legal",
        ),
    }
    return JSONResponse(manifest)


@app.get("/.well-known/openapi.json", include_in_schema=False)
async def well_known_openapi() -> JSONResponse:
    """
    Convenience alias for clients that look under /.well-known/.
    """
    return JSONResponse(app.openapi())


# Mount MCP last so normal FastAPI routes remain available.
app.mount("/mcp", mcp_app, name="mcp")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
