# Magic-PDF: MCP Server for PDF Operations

## 1. Project Overview

An open-source MCP (Model Context Protocol) server that provides comprehensive PDF manipulation tools. Designed to run locally with no authentication, exposing PDF operations as MCP tools that any MCP-compatible client (Claude Desktop, VS Code, Cursor, etc.) can invoke.

## 2. Technical Stack & Standards

- **Language:** Python 3.10+
- **MCP Framework:** FastMCP (via `mcp[cli]` SDK)
- **Transport:** stdio (standard for local MCP servers)
- **Package Manager:** `uv` (industry standard for MCP Python projects)
- **Authentication:** None (local-only server)
- **Project Structure:**
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

## 3. Setup & Installation

- One-command install via `uv` or `pip`
- All Python dependencies bundled via `pyproject.toml`
- **Office Conversion Strategy: Hybrid**
  - Use LibreOffice headless when available for high-fidelity DOCX/Excel/PPT conversion
  - Fall back to pure Python libraries (`python-docx`, `openpyxl`, `python-pptx` + `reportlab`) when LibreOffice is not installed
  - Log a warning when falling back, informing the user that fidelity may be reduced
  - README documents optional LibreOffice install for best results
- MCP client configuration example provided in README (e.g., Claude Desktop `claude_desktop_config.json`)

## 4. MCP Tools

### 4.1 PDF Reading & Info
- **`read_pdf`** — Extract text content from a PDF and return it. Supports optional page range parameter to read specific pages.
- **`get_pdf_info`** — Return PDF metadata: page count, file size, page dimensions, encryption status, and document properties (author, title, creation date) when available.

### 4.2 PDF Creation
- **`create_pdf_from_text`** — Create a PDF from text input. Supports Markdown formatting (headings, bold, italic, lists, etc.). Also accepts optional parameters for font, font size, page size (A4/Letter), and margins.

### 4.3 Format Conversion (to PDF)
- **`docx_to_pdf`** — Convert Word documents (.docx) to PDF
- **`image_to_pdf`** — Convert image(s) to PDF. Supported formats: JPEG, PNG, BMP, TIFF, GIF
- **`html_to_pdf`** — Convert HTML to PDF. Accepts either:
  - A raw HTML string
  - A URL to fetch and convert
- **`excel_to_pdf`** — Convert Excel spreadsheets (.xlsx/.xls) to PDF
- **`powerpoint_to_pdf`** — Convert PowerPoint presentations (.pptx/.ppt) to PDF

### 4.4 Format Conversion (from PDF)
- **`pdf_to_image`** — Convert PDF page(s) to images. Supports output format (PNG, JPEG) and optional DPI setting. Can convert a single page or all pages.

### 4.5 PDF Manipulation
- **`merge_pdfs`** — Merge multiple PDF files into one
- **`split_pdf`** — Split a PDF into multiple files (by page range or individual pages)

### 4.6 Page Organization
- **`add_pages`** — Insert pages into a PDF
- **`remove_pages`** — Remove specific pages from a PDF
- **`move_pages`** — Reorder pages within a PDF
- **`separate_pages`** — Extract specific pages into a new PDF

### 4.7 Compression
- **`compress_pdf`** — Compress a PDF with named compression levels:
  - **`low`** — Lossless compression, remove duplicate objects/streams. Minimal quality loss.
  - **`medium`** — Downsample images to 150 DPI, compress streams. Good balance.
  - **`high`** — Downsample images to 72 DPI, strip metadata, aggressive compression. Smallest file size.

### 4.8 Search
- **`search_pdf`** — Search for text within a PDF (embedded text layer only, no OCR). Returns:
  - Match count
  - Page numbers where matches occur
  - Matching text with surrounding context snippets

### 4.9 PDF Forms
- **`get_form_fields`** — List all form fields in a PDF with their names, types (text, checkbox, dropdown, radio), and current values.
- **`fill_form`** — Populate form fields by providing a dictionary of field names to values.
- **`flatten_form`** — Convert filled form fields into static PDF content so they can no longer be edited.

### 4.10 Modification
- **`add_header_footer`** — Add headers and/or footers to PDF pages. Supports:
  - Dynamic placeholders: `{page_number}`, `{total_pages}`, `{date}`
  - Font, font size, and alignment (left/center/right) options
- **`redact_pdf`** — Redact content from a PDF. Supports two modes:
  - **Text-based:** Provide a search term or regex; all matches are blacked out and removed from the text layer
  - **Area-based:** Provide page number and coordinates (x, y, width, height) to redact a rectangular region

## 5. File I/O Convention

- All tools accept an input file path (absolute)
- Output path is **optional** — if not provided, save to the same directory as the input with a descriptive suffix (e.g., `document_compressed.pdf`, `document_merged.pdf`, `document_redacted.pdf`)
- For tools that produce multiple outputs (e.g., `split_pdf`), create files with numbered suffixes (e.g., `document_part1.pdf`, `document_part2.pdf`)

## 6. Error Handling

- File existence and permission validation before any operation
- File size limits with clear error messages
- File type / extension validation
- Graceful handling of corrupted or password-protected PDFs
- Structured error responses following MCP conventions
- Logging to stderr (required for stdio-based MCP servers)

## 7. Resolved Decisions

- [x] Office conversion dependency strategy — **Hybrid** (LibreOffice preferred, pure Python fallback)
- [x] Compression levels — **Named tiers** (`low`, `medium`, `high`)
- [x] Search — **Text-only** (embedded text layer, no OCR)
- [x] Redaction — **Both** (text-based via search/regex + area-based via coordinates)
- [x] License — **MIT**
- [x] Image-to-PDF — **Standard set** (JPEG, PNG, BMP, TIFF, GIF)
- [x] HTML-to-PDF — **Both** (raw HTML string or URL)
