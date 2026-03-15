"""PDF creation and reading tools."""

import os
import re

import pypdf
import markdown
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet

from .utils import (
    validate_pdf_file,
    validate_file_size,
    ensure_output_dir,
    logger,
)


def read_pdf(
    file_path: str,
    start_page: int | None = None,
    end_page: int | None = None,
) -> str:
    """Extract text content from a PDF. Supports optional page range (1-indexed).

    Args:
        file_path: Absolute path to the PDF file
        start_page: First page to read (1-indexed, default: first page)
        end_page: Last page to read (1-indexed, inclusive, default: last page)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    reader = pypdf.PdfReader(file_path)
    total_pages = len(reader.pages)

    if total_pages == 0:
        return "PDF has no pages."

    start = (start_page or 1) - 1
    end = end_page or total_pages

    if start < 0 or end > total_pages or start >= end:
        raise ValueError(
            f"Invalid page range: {start_page}-{end_page} "
            f"(PDF has {total_pages} pages)"
        )

    text_parts = []
    for i in range(start, end):
        page_text = reader.pages[i].extract_text() or ""
        text_parts.append(f"--- Page {i + 1} ---\n{page_text}")

    return "\n\n".join(text_parts)


def get_pdf_info(file_path: str) -> dict:
    """Return PDF metadata: page count, file size, page dimensions, encryption status, and document properties.

    Args:
        file_path: Absolute path to the PDF file
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    reader = pypdf.PdfReader(file_path)
    file_size = os.path.getsize(file_path)

    info = {
        "page_count": len(reader.pages),
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "encrypted": reader.is_encrypted,
    }

    # Page dimensions from first page
    if reader.pages:
        page = reader.pages[0]
        box = page.mediabox
        info["page_width_pt"] = float(box.width)
        info["page_height_pt"] = float(box.height)
        info["page_width_in"] = round(float(box.width) / 72, 2)
        info["page_height_in"] = round(float(box.height) / 72, 2)

    # Document properties
    meta = reader.metadata
    if meta:
        info["properties"] = {
            "author": meta.author,
            "title": meta.title,
            "subject": meta.subject,
            "creator": meta.creator,
            "producer": meta.producer,
            "creation_date": str(meta.creation_date) if meta.creation_date else None,
            "modification_date": (
                str(meta.modification_date) if meta.modification_date else None
            ),
        }

    return info


def create_pdf_from_text(
    text: str,
    output_path: str,
    font: str = "Helvetica",
    font_size: int = 12,
    page_size: str = "A4",
    margin_top: float = 72,
    margin_bottom: float = 72,
    margin_left: float = 72,
    margin_right: float = 72,
) -> str:
    """Create a PDF from text input. Supports Markdown formatting (headings, bold, italic, lists).

    Args:
        text: Text content, optionally with Markdown formatting
        output_path: Absolute path for the output PDF file
        font: Font name (default: Helvetica)
        font_size: Base font size in points (default: 12)
        page_size: Page size - 'A4' or 'Letter' (default: A4)
        margin_top: Top margin in points (default: 72 = 1 inch)
        margin_bottom: Bottom margin in points (default: 72)
        margin_left: Left margin in points (default: 72)
        margin_right: Right margin in points (default: 72)
    """
    ensure_output_dir(output_path)

    sizes = {"a4": A4, "letter": letter}
    selected_size = sizes.get(page_size.lower(), A4)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=selected_size,
        topMargin=margin_top,
        bottomMargin=margin_bottom,
        leftMargin=margin_left,
        rightMargin=margin_right,
    )

    styles = getSampleStyleSheet()

    # Convert markdown to HTML
    html = markdown.markdown(text, extensions=["extra", "sane_lists"])

    # Parse HTML into reportlab flowables
    story = _html_to_flowables(html, styles)

    if not story:
        # Fallback: treat as plain text
        story = [Paragraph(text.replace("\n", "<br/>"), styles["Normal"])]

    doc.build(story)
    return f"PDF created: {output_path}"


def _html_to_flowables(html: str, styles) -> list:
    """Convert simple HTML (from markdown) into reportlab flowables."""
    story = []

    # Split by block-level tags
    blocks = re.split(
        r"(<h[1-6][^>]*>.*?</h[1-6]>|<p>.*?</p>|<ul>.*?</ul>|<ol>.*?</ol>)",
        html,
        flags=re.DOTALL,
    )

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Headings
        h_match = re.match(r"<h(\d)[^>]*>(.*?)</h\d>", block, re.DOTALL)
        if h_match:
            level = int(h_match.group(1))
            content = h_match.group(2)
            style_name = f"Heading{min(level, 6)}"
            style = styles.get(style_name, styles["Heading1"])
            story.append(Paragraph(content, style))
            story.append(Spacer(1, 6))
            continue

        # Paragraphs
        p_match = re.match(r"<p>(.*?)</p>", block, re.DOTALL)
        if p_match:
            content = p_match.group(1)
            story.append(Paragraph(content, styles["Normal"]))
            story.append(Spacer(1, 6))
            continue

        # Lists (ul/ol)
        ul_match = re.match(r"<(ul|ol)>(.*?)</\1>", block, re.DOTALL)
        if ul_match:
            list_type = ul_match.group(1)
            items_html = ul_match.group(2)
            items = re.findall(r"<li>(.*?)</li>", items_html, re.DOTALL)
            bullet_type = "bullet" if list_type == "ul" else "1"
            list_items = []
            for item in items:
                list_items.append(ListItem(Paragraph(item, styles["Normal"])))
            if list_items:
                story.append(ListFlowable(list_items, bulletType=bullet_type))
                story.append(Spacer(1, 6))
            continue

        # Fallback: treat as paragraph if it has content
        if block and not block.startswith("<"):
            story.append(Paragraph(block, styles["Normal"]))
            story.append(Spacer(1, 6))

    return story


def register(mcp):
    """Register PDF creation and reading tools with the MCP server."""
    mcp.tool()(read_pdf)
    mcp.tool()(get_pdf_info)
    mcp.tool()(create_pdf_from_text)
