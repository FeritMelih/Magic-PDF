# Magic-PDF

An open-source MCP (Model Context Protocol) server for comprehensive PDF operations. Run it locally and connect it to any MCP-compatible client — Claude Desktop, VS Code, Cursor, and more.

## Features

**23 tools** across 10 categories:

| Category | Tools |
|---|---|
| **Reading & Info** | `read_pdf`, `get_pdf_info` |
| **Creation** | `create_pdf_from_text` (Markdown, custom fonts/sizing) |
| **Convert to PDF** | `docx_to_pdf`, `image_to_pdf`, `html_to_pdf`, `excel_to_pdf`, `powerpoint_to_pdf` |
| **Convert from PDF** | `pdf_to_image` |
| **Manipulation** | `merge_pdfs`, `split_pdf` |
| **Page Organization** | `add_pages`, `remove_pages`, `move_pages`, `separate_pages` |
| **Compression** | `compress_pdf` (low / medium / high) |
| **Search** | `search_pdf` (with context snippets) |
| **Forms** | `get_form_fields`, `fill_form`, `flatten_form` |
| **Modification** | `add_header_footer`, `redact_pdf` |

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- **Optional:** [LibreOffice](https://www.libreoffice.org/) for high-fidelity Office document conversion (DOCX, Excel, PowerPoint). Without it, the server falls back to pure Python libraries with reduced formatting fidelity.

### Installing LibreOffice

LibreOffice is optional but recommended for best results when converting DOCX, Excel, and PowerPoint files to PDF.

**Windows:**
```bash
winget install --id TheDocumentFoundation.LibreOffice
```

**macOS:**
```bash
brew install --cask libreoffice
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install libreoffice
```

The server auto-detects LibreOffice at startup — no additional configuration is needed. It searches `PATH` for `libreoffice`/`soffice` and checks common install locations on Windows.

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/magic-pdf.git
cd magic-pdf

# Install with uv (recommended)
uv venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
uv pip install -e .

# Or install with pip
pip install -e .
```

## Usage

### Running the server

```bash
# With uv
uv run magic-pdf

# Or directly
python -m magic_pdf
```

### Connecting to Claude Desktop

Add the following to your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "magic-pdf": {
      "command": "uv",
      "args": ["--directory", "/path/to/magic-pdf", "run", "magic-pdf"]
    }
  }
}
```

### Connecting to VS Code / Cursor

Add to your `.vscode/mcp.json` or Cursor MCP settings:

```json
{
  "servers": {
    "magic-pdf": {
      "command": "uv",
      "args": ["--directory", "/path/to/magic-pdf", "run", "magic-pdf"]
    }
  }
}
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Test with MCP Inspector
mcp dev src/magic_pdf/server.py
```

## Project Structure

```
magic-pdf/
├── src/
│   └── magic_pdf/
│       ├── __init__.py
│       ├── server.py          # FastMCP server entry point
│       └── tools/
│           ├── __init__.py
│           ├── create.py       # PDF creation tools
│           ├── convert.py      # Format conversion tools
│           ├── manipulate.py   # Merge, split, organize tools
│           ├── compress.py     # Compression tools
│           ├── search.py       # Search tools
│           ├── modify.py       # Header/footer, redact tools
│           ├── forms.py        # PDF form tools
│           └── utils.py        # Shared utilities & validation
├── tests/
├── pyproject.toml
├── README.md
└── LICENSE
```

## License

[MIT](LICENSE)
