from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastmcp import FastMCP

from .client import PaperclipClient, Settings
from .registry import ToolRegistrar
from .tools import register_all_tools

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] paperclip-mcp %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)


def validate_config(settings: Settings) -> None:
    missing = [
        name
        for name, value in {
            "PAPERCLIP_API_KEY": settings.api_key,
            "PAPERCLIP_COMPANY_ID": settings.company_id,
        }.items()
        if not value
    ]
    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        log.error("Copy .env.example to .env, fill in the values, then start paperclip-mcp.")
        sys.exit(1)


settings = Settings.from_env()


def make_lifespan(
    server_settings: Settings,
) -> Callable[[FastMCP], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def server_lifespan(_server: FastMCP) -> AsyncIterator[None]:
        validate_config(server_settings)
        log.info(
            "paperclip-mcp started — base: %s | company: %s",
            server_settings.base_url,
            server_settings.company_id,
        )
        yield
        log.info("paperclip-mcp stopped.")

    return server_lifespan


def create_server(server_settings: Settings | None = None) -> FastMCP:
    active_settings = settings if server_settings is None else server_settings
    server = FastMCP(
        name="paperclip",
        instructions=(
            "Manage Paperclip issues, agents, goals, projects, approvals, routines, secrets, "
            "companies, and monitoring. Operations use PAPERCLIP_COMPANY_ID by default."
        ),
        lifespan=make_lifespan(active_settings),
    )
    register_all_tools(
        ToolRegistrar(server, active_settings.disabled_tools),
        PaperclipClient(active_settings),
        active_settings.company_id,
    )
    return server


mcp = create_server()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="paperclip-mcp",
        description="MCP server for the Paperclip AI agent orchestration platform.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address. Use 0.0.0.0 only in trusted local networks.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9011,
        help="Bind port.",
    )
    parser.add_argument(
        "--transport",
        default="streamable-http",
        choices=["streamable-http", "sse", "stdio"],
        help=(
            "MCP transport protocol. "
            "'streamable-http' for Claude Code / mcp-proxy; "
            "'stdio' for Claude Desktop."
        ),
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
