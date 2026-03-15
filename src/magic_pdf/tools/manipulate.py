"""PDF manipulation tools: merge, split, and page organization."""

import os

import pypdf

from .utils import (
    validate_pdf_file,
    validate_file_size,
    generate_output_path,
    ensure_output_dir,
)


def merge_pdfs(file_paths: list[str], output_path: str) -> str:
    """Merge multiple PDF files into one.

    Args:
        file_paths: List of absolute paths to PDF files (in merge order)
        output_path: Absolute path for the merged output PDF
    """
    if not file_paths or len(file_paths) < 2:
        raise ValueError("At least 2 PDF files are required for merging")

    for fp in file_paths:
        validate_pdf_file(fp)
        validate_file_size(fp)

    ensure_output_dir(output_path)

    writer = pypdf.PdfWriter()
    for fp in file_paths:
        reader = pypdf.PdfReader(fp)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    total_pages = len(writer.pages)
    return f"Merged {len(file_paths)} PDFs ({total_pages} pages) into: {output_path}"


def split_pdf(
    file_path: str,
    ranges: list[str],
    output_dir: str | None = None,
) -> str:
    """Split a PDF into multiple files by page ranges.

    Args:
        file_path: Absolute path to the PDF file
        ranges: List of page range strings, e.g. ['1-3', '4-6', '7'] for specific ranges,
                or ['individual'] to split every page into its own file
        output_dir: Directory for output files (default: same as input file)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    reader = pypdf.PdfReader(file_path)
    total_pages = len(reader.pages)

    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_files = []

    if ranges == ["individual"]:
        # Split every page into its own file
        for i in range(total_pages):
            writer = pypdf.PdfWriter()
            writer.add_page(reader.pages[i])
            out_path = os.path.join(output_dir, f"{base_name}_page{i + 1}.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            output_files.append(out_path)
    else:
        for idx, page_range in enumerate(ranges, 1):
            writer = pypdf.PdfWriter()

            if "-" in page_range:
                start, end = page_range.split("-", 1)
                start_idx = int(start) - 1
                end_idx = int(end)
                if start_idx < 0 or end_idx > total_pages:
                    raise ValueError(
                        f"Invalid range '{page_range}' (PDF has {total_pages} pages)"
                    )
                for i in range(start_idx, end_idx):
                    writer.add_page(reader.pages[i])
            else:
                page_idx = int(page_range) - 1
                if page_idx < 0 or page_idx >= total_pages:
                    raise ValueError(
                        f"Invalid page '{page_range}' (PDF has {total_pages} pages)"
                    )
                writer.add_page(reader.pages[page_idx])

            out_path = os.path.join(output_dir, f"{base_name}_part{idx}.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            output_files.append(out_path)

    return f"Split into {len(output_files)} files: {', '.join(output_files)}"


def add_pages(
    file_path: str,
    insert_file_path: str,
    position: int,
    output_path: str | None = None,
) -> str:
    """Insert pages from another PDF into a PDF at a specified position.

    Args:
        file_path: Absolute path to the target PDF
        insert_file_path: Absolute path to the PDF containing pages to insert
        position: Position to insert at (1-indexed, pages are inserted before this position)
        output_path: Optional output path (default: overwrites with suffix)
    """
    validate_pdf_file(file_path)
    validate_pdf_file(insert_file_path)
    validate_file_size(file_path)
    validate_file_size(insert_file_path)

    if output_path is None:
        output_path = generate_output_path(file_path, "inserted")
    ensure_output_dir(output_path)

    reader = pypdf.PdfReader(file_path)
    insert_reader = pypdf.PdfReader(insert_file_path)
    writer = pypdf.PdfWriter()

    insert_idx = max(0, min(position - 1, len(reader.pages)))

    for i in range(insert_idx):
        writer.add_page(reader.pages[i])

    for page in insert_reader.pages:
        writer.add_page(page)

    for i in range(insert_idx, len(reader.pages)):
        writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

    return (
        f"Inserted {len(insert_reader.pages)} pages at position {position}: {output_path}"
    )


def remove_pages(
    file_path: str,
    pages: list[int],
    output_path: str | None = None,
) -> str:
    """Remove specific pages from a PDF.

    Args:
        file_path: Absolute path to the PDF file
        pages: List of page numbers to remove (1-indexed)
        output_path: Optional output path (default: same directory with suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if output_path is None:
        output_path = generate_output_path(file_path, "removed")
    ensure_output_dir(output_path)

    reader = pypdf.PdfReader(file_path)
    total_pages = len(reader.pages)

    pages_to_remove = set()
    for p in pages:
        if p < 1 or p > total_pages:
            raise ValueError(f"Invalid page number {p} (PDF has {total_pages} pages)")
        pages_to_remove.add(p - 1)  # Convert to 0-indexed

    if len(pages_to_remove) >= total_pages:
        raise ValueError("Cannot remove all pages from a PDF")

    writer = pypdf.PdfWriter()
    for i in range(total_pages):
        if i not in pages_to_remove:
            writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

    return f"Removed {len(pages_to_remove)} pages: {output_path}"


def move_pages(
    file_path: str,
    page_order: list[int],
    output_path: str | None = None,
) -> str:
    """Reorder pages within a PDF.

    Args:
        file_path: Absolute path to the PDF file
        page_order: New page order as list of page numbers (1-indexed).
                    E.g. [3, 1, 2] moves page 3 to first position.
        output_path: Optional output path (default: same directory with suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if output_path is None:
        output_path = generate_output_path(file_path, "reordered")
    ensure_output_dir(output_path)

    reader = pypdf.PdfReader(file_path)
    total_pages = len(reader.pages)

    # Validate page order
    for p in page_order:
        if p < 1 or p > total_pages:
            raise ValueError(f"Invalid page number {p} (PDF has {total_pages} pages)")

    writer = pypdf.PdfWriter()
    for p in page_order:
        writer.add_page(reader.pages[p - 1])

    with open(output_path, "wb") as f:
        writer.write(f)

    return f"Reordered {len(page_order)} pages: {output_path}"


def separate_pages(
    file_path: str,
    pages: list[int],
    output_path: str | None = None,
) -> str:
    """Extract specific pages into a new PDF.

    Args:
        file_path: Absolute path to the PDF file
        pages: List of page numbers to extract (1-indexed)
        output_path: Optional output path (default: same directory with suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if output_path is None:
        output_path = generate_output_path(file_path, "extracted")
    ensure_output_dir(output_path)

    reader = pypdf.PdfReader(file_path)
    total_pages = len(reader.pages)

    writer = pypdf.PdfWriter()
    for p in pages:
        if p < 1 or p > total_pages:
            raise ValueError(f"Invalid page number {p} (PDF has {total_pages} pages)")
        writer.add_page(reader.pages[p - 1])

    with open(output_path, "wb") as f:
        writer.write(f)

    return f"Extracted {len(pages)} pages: {output_path}"


def register(mcp):
    """Register PDF manipulation tools with the MCP server."""
    mcp.tool()(merge_pdfs)
    mcp.tool()(split_pdf)
    mcp.tool()(add_pages)
    mcp.tool()(remove_pages)
    mcp.tool()(move_pages)
    mcp.tool()(separate_pages)
