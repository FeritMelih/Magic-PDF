"""PDF modification tools: headers/footers and redaction."""

import re
from datetime import datetime

import fitz  # PyMuPDF

# Substitution map for characters outside Latin-1 range (0x00-0xFF)
_UNICODE_SUBS = {
    "\u2014": "--",   # em dash
    "\u2013": "-",    # en dash
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u2026": "...",  # ellipsis
    "\u2022": "*",    # bullet
    "\u00b7": "*",    # middle dot (Latin-1 but often problematic)
    "\u2010": "-",    # hyphen
    "\u2011": "-",    # non-breaking hyphen
    "\u2012": "-",    # figure dash
    "\u2015": "--",   # horizontal bar
    "\u2032": "'",    # prime
    "\u2033": '"',    # double prime
    "\u00a0": " ",    # non-breaking space
}


def _sanitize_for_latin1(text: str) -> str:
    """Replace non-Latin-1 characters with ASCII equivalents."""
    result = []
    for ch in text:
        if ord(ch) <= 0xFF:
            result.append(ch)
        elif ch in _UNICODE_SUBS:
            result.append(_UNICODE_SUBS[ch])
        else:
            result.append("?")
    return "".join(result)

from .utils import (
    validate_pdf_file,
    validate_file_size,
    generate_output_path,
    ensure_output_dir,
)


def add_header_footer(
    file_path: str,
    header: str | None = None,
    footer: str | None = None,
    font: str = "helv",
    font_size: float = 10,
    alignment: str = "center",
    output_path: str | None = None,
) -> str:
    """Add headers and/or footers to PDF pages.

    Supports dynamic placeholders: {page_number}, {total_pages}, {date}

    Args:
        file_path: Absolute path to the PDF file
        header: Header text (supports placeholders)
        footer: Footer text (supports placeholders)
        font: Font name (default: helv). Options: helv, tiro, cour, symb, zadb
        font_size: Font size in points (default: 10)
        alignment: Text alignment - 'left', 'center', or 'right' (default: center)
        output_path: Optional output path (default: same directory with suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if header is None and footer is None:
        raise ValueError("At least one of header or footer must be provided")

    if output_path is None:
        output_path = generate_output_path(file_path, "headerfooter")
    ensure_output_dir(output_path)

    align_map = {
        "left": fitz.TEXT_ALIGN_LEFT,
        "center": fitz.TEXT_ALIGN_CENTER,
        "right": fitz.TEXT_ALIGN_RIGHT,
    }
    text_align = align_map.get(alignment.lower(), fitz.TEXT_ALIGN_CENTER)

    doc = fitz.open(file_path)
    total_pages = len(doc)
    today = datetime.now().strftime("%Y-%m-%d")

    for page_num, page in enumerate(doc, 1):
        rect = page.rect

        def _apply_placeholders(text: str) -> str:
            return (
                text.replace("{page_number}", str(page_num))
                .replace("{total_pages}", str(total_pages))
                .replace("{date}", today)
            )

        if header:
            header_text = _sanitize_for_latin1(_apply_placeholders(header))
            header_rect = fitz.Rect(
                50, 20, rect.width - 50, 20 + font_size + 10
            )
            page.insert_textbox(
                header_rect,
                header_text,
                fontname=font,
                fontsize=font_size,
                align=text_align,
            )

        if footer:
            footer_text = _sanitize_for_latin1(_apply_placeholders(footer))
            footer_rect = fitz.Rect(
                50,
                rect.height - 20 - font_size - 10,
                rect.width - 50,
                rect.height - 20,
            )
            page.insert_textbox(
                footer_rect,
                footer_text,
                fontname=font,
                fontsize=font_size,
                align=text_align,
            )

    doc.save(output_path)
    doc.close()

    parts = []
    if header:
        parts.append("header")
    if footer:
        parts.append("footer")
    return f"Added {' and '.join(parts)} to {total_pages} pages: {output_path}"


def redact_pdf(
    file_path: str,
    search_text: str | None = None,
    use_regex: bool = False,
    areas: list[dict] | None = None,
    output_path: str | None = None,
) -> str:
    """Redact content from a PDF. Supports text-based and area-based redaction.

    Args:
        file_path: Absolute path to the PDF file
        search_text: Text or regex pattern to find and redact
        use_regex: Whether search_text is a regex pattern (default: False)
        areas: List of area dicts with keys: page (1-indexed), x, y, width, height (in points)
        output_path: Optional output path (default: same directory with suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if search_text is None and areas is None:
        raise ValueError("At least one of search_text or areas must be provided")

    if output_path is None:
        output_path = generate_output_path(file_path, "redacted")
    ensure_output_dir(output_path)

    doc = fitz.open(file_path)
    redaction_count = 0

    # Text-based redaction
    if search_text:
        for page in doc:
            if use_regex:
                # Extract full page text and find all regex matches
                page_text = page.get_text()
                seen_matches = set()
                for m in re.finditer(search_text, page_text):
                    matched_text = m.group()
                    if matched_text in seen_matches:
                        continue
                    seen_matches.add(matched_text)
                    # Use page.search_for() to get precise bounding rects
                    rects = page.search_for(matched_text)
                    for rect in rects:
                        page.add_redact_annot(rect, fill=(0, 0, 0))
                        redaction_count += 1
            else:
                instances = page.search_for(search_text)
                for rect in instances:
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                    redaction_count += 1

            page.apply_redactions()

    # Area-based redaction
    if areas:
        for area in areas:
            page_num = area.get("page", 1) - 1
            if page_num < 0 or page_num >= len(doc):
                raise ValueError(
                    f"Invalid page number {area.get('page')} "
                    f"(PDF has {len(doc)} pages)"
                )
            page = doc[page_num]
            rect = fitz.Rect(
                area["x"],
                area["y"],
                area["x"] + area["width"],
                area["y"] + area["height"],
            )
            page.add_redact_annot(rect, fill=(0, 0, 0))
            page.apply_redactions()
            redaction_count += 1

    doc.save(output_path)
    doc.close()

    return f"Applied {redaction_count} redaction(s): {output_path}"


def register(mcp):
    """Register modification tools with the MCP server."""
    mcp.tool()(add_header_footer)
    mcp.tool()(redact_pdf)
