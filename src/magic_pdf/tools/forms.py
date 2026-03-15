"""PDF form tools."""

import fitz  # PyMuPDF
import pypdf

from .utils import (
    validate_pdf_file,
    validate_file_size,
    generate_output_path,
    ensure_output_dir,
)


def get_form_fields(file_path: str) -> dict:
    """List all form fields in a PDF with their names, types, and current values.

    Args:
        file_path: Absolute path to the PDF file

    Returns:
        Dict with field count and list of field details (name, type, value)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    reader = pypdf.PdfReader(file_path)
    fields = reader.get_fields()

    if not fields:
        return {"field_count": 0, "fields": [], "message": "No form fields found"}

    field_type_map = {
        "/Tx": "text",
        "/Btn": "checkbox/radio",
        "/Ch": "dropdown",
        "/Sig": "signature",
    }

    field_list = []
    for name, field in fields.items():
        ft = field.get("/FT", "unknown")
        field_info = {
            "name": name,
            "type": field_type_map.get(ft, str(ft)),
            "value": field.get("/V", None),
        }

        # For checkbox/radio, check if it has specific options
        if ft == "/Btn":
            if "/AP" in field and "/N" in field["/AP"]:
                field_info["options"] = list(field["/AP"]["/N"].keys())

        # For dropdown/choice fields
        if ft == "/Ch" and "/Opt" in field:
            field_info["options"] = [
                str(opt) for opt in field["/Opt"]
            ]

        field_list.append(field_info)

    return {"field_count": len(field_list), "fields": field_list}


def fill_form(
    file_path: str,
    fields: dict[str, str],
    output_path: str | None = None,
) -> str:
    """Populate form fields by providing a dictionary of field names to values.

    Args:
        file_path: Absolute path to the PDF file
        fields: Dictionary mapping field names to values
        output_path: Optional output path (default: same directory with suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if not fields:
        raise ValueError("No fields provided to fill")

    if output_path is None:
        output_path = generate_output_path(file_path, "filled")
    ensure_output_dir(output_path)

    reader = pypdf.PdfReader(file_path)
    writer = pypdf.PdfWriter()
    writer.append(reader)

    # Update form field values on all pages
    for page_num in range(len(writer.pages)):
        writer.update_page_form_field_values(writer.pages[page_num], fields)

    with open(output_path, "wb") as f:
        writer.write(f)

    return f"Filled {len(fields)} form field(s): {output_path}"


def flatten_form(
    file_path: str,
    output_path: str | None = None,
) -> str:
    """Convert filled form fields into static PDF content so they can no longer be edited.

    Args:
        file_path: Absolute path to the PDF file
        output_path: Optional output path (default: same directory with suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if output_path is None:
        output_path = generate_output_path(file_path, "flattened")
    ensure_output_dir(output_path)

    # Use PyMuPDF to flatten by rendering pages to a new document
    doc = fitz.open(file_path)
    new_doc = fitz.open()

    for page in doc:
        # Create new page with same dimensions
        new_page = new_doc.new_page(
            width=page.rect.width, height=page.rect.height
        )
        # Render original page (including form field values) into new page
        new_page.show_pdf_page(page.rect, doc, page.number)

    new_doc.save(output_path)
    new_doc.close()
    doc.close()

    return f"Form flattened: {output_path}"


def register(mcp):
    """Register PDF form tools with the MCP server."""
    mcp.tool()(get_form_fields)
    mcp.tool()(fill_form)
    mcp.tool()(flatten_form)
