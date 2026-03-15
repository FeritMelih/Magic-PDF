"""PDF search tools."""

import pypdf

from .utils import validate_pdf_file, validate_file_size


def search_pdf(
    file_path: str,
    query: str,
    case_sensitive: bool = False,
    context_chars: int = 50,
) -> dict:
    """Search for text within a PDF (embedded text layer only, no OCR).

    Args:
        file_path: Absolute path to the PDF file
        query: Text to search for
        case_sensitive: Whether the search is case-sensitive (default: False)
        context_chars: Number of characters of context around each match (default: 50)

    Returns:
        Dict with match_count, pages, and matches with context snippets
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if not query:
        raise ValueError("Search query cannot be empty")

    reader = pypdf.PdfReader(file_path)
    matches = []
    page_numbers = set()

    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""

        search_text = text if case_sensitive else text.lower()
        search_query = query if case_sensitive else query.lower()

        start = 0
        while True:
            idx = search_text.find(search_query, start)
            if idx == -1:
                break

            page_numbers.add(page_num)

            # Extract context
            ctx_start = max(0, idx - context_chars)
            ctx_end = min(len(text), idx + len(query) + context_chars)
            context = text[ctx_start:ctx_end]

            # Add ellipsis for truncated context
            prefix = "..." if ctx_start > 0 else ""
            suffix = "..." if ctx_end < len(text) else ""

            matches.append(
                {
                    "page": page_num,
                    "context": f"{prefix}{context}{suffix}",
                    "position": idx,
                }
            )

            start = idx + 1

    return {
        "query": query,
        "match_count": len(matches),
        "pages": sorted(page_numbers),
        "matches": matches,
    }


def register(mcp):
    """Register search tools with the MCP server."""
    mcp.tool()(search_pdf)
