"""FastMCP server entry point for Magic-PDF."""

import sys
import logging

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (required for stdio-based MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

mcp = FastMCP("Magic-PDF")

# Register all tool modules
from .tools import create, convert, manipulate, compress, search, modify, forms

create.register(mcp)
convert.register(mcp)
manipulate.register(mcp)
compress.register(mcp)
search.register(mcp)
modify.register(mcp)
forms.register(mcp)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
