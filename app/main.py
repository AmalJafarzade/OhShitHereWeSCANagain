from __future__ import annotations

import asyncio
import shlex
import shutil
from pathlib import Path
from typing import AsyncGenerator, TypedDict
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "static"

app = FastAPI(
    title="Local Recon Orchestrator",
    description=(
        "Run your locally installed reconnaissance tools from a single UI. "
        "Outputs stream in real time and every endpoint is documented via Swagger."
    ),
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/swagger/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolInfo(TypedDict):
    name: str
    binary: str
    description: str
    available: bool


TOOLS = {
    "fuzz": {
        "binary": "fuzz",
        "description": "Generic fuzzing helper. Ensure the binary is available locally.",
    },
    "nmap": {"binary": "nmap", "description": "Port scanner and service detector."},
    "dirsearch": {
        "binary": "dirsearch",
        "description": "Directory brute forcer for web paths.",
    },
    "theHarvester": {
        "binary": "theHarvester",
        "description": "Open source intelligence gathering tool.",
    },
    "Subfinder": {
        "binary": "subfinder",
        "description": "Passive subdomain enumeration.",
    },
    "httpx": {
        "binary": "httpx",
        "description": "HTTP probing tool for discovering live hosts.",
    },
    "dalfox": {"binary": "dalfox", "description": "XSS scanning utility."},
    "nuclei": {
        "binary": "nuclei",
        "description": "Fast template-based vulnerability scanner.",
    },
    "sublist3r": {
        "binary": "sublist3r",
        "description": "Fast subdomains enumeration tool.",
    },
}


@app.get("/tools")
async def list_tools() -> list[ToolInfo]:
    """Return the configured tools along with their binaries and descriptions."""

    return [
        {
            "name": name,
            "binary": cfg["binary"],
            "description": cfg["description"],
            "available": shutil.which(cfg["binary"]) is not None,
        }
async def list_tools() -> list[dict[str, str]]:
    """Return the configured tools along with their binaries and descriptions."""

    return [
        {"name": name, "binary": cfg["binary"], "description": cfg["description"]}
        for name, cfg in TOOLS.items()
    ]


async def stream_command(command: list[str]) -> AsyncGenerator[str, None]:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    banner = f"$ {' '.join(shlex.quote(part) for part in command)}\n"
    yield f"data: {banner}\n\n"

    assert process.stdout is not None
    async for raw_line in process.stdout:
        line = raw_line.decode(errors="ignore").rstrip()
        yield f"data: {line}\n\n"

    return_code = await process.wait()
    yield f"data: [process exited with status {return_code}]\n\n"


@app.get(
    "/run/{tool_name}",
    responses={
        200: {"content": {"text/event-stream": {}}},
        404: {"description": "Tool not found"},
    },
)
async def run_tool(
    tool_name: str,
    target: str | None = Query(default=None, description="Primary target such as a domain"),
    args: list[str] = Query(default_factory=list, description="Extra CLI arguments"),
) -> StreamingResponse:
    """
    Stream the output of a configured tool.

    Parameters are passed directly to the local binary. Use responsibly and ensure each
    tool is installed on the host where this API runs.
    """

    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail="Unknown tool")

    binary = shutil.which(TOOLS[tool_name]["binary"])
    if not binary:
        raise HTTPException(
            status_code=400,
            detail=f"Binary '{TOOLS[tool_name]['binary']}' was not found in PATH. Install it or update the TOOLS mapping.",
        )

    command = [binary]
    command = [TOOLS[tool_name]["binary"]]
    command.extend(args)
    if target:
        command.append(target)

    return StreamingResponse(stream_command(command), media_type="text/event-stream")


@app.get("/")
async def serve_ui() -> FileResponse:
    """Serve the minimal UI that orchestrates tool runs."""

    return FileResponse(STATIC_DIR / "index.html")


@app.get("/swagger", include_in_schema=False)
async def overridden_swagger() -> StreamingResponse:
    """Serve Swagger UI backed by the generated OpenAPI schema."""

    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url="/swagger/oauth2-redirect",
    )


@app.get("/swagger/oauth2-redirect", include_in_schema=False)
async def swagger_redirect() -> StreamingResponse:
    return get_swagger_ui_oauth2_redirect_html()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
