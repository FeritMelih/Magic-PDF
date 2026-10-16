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

    message = f"Filled {len(fields)} form field(s): {output_path}"
    overflowing = overflowing_fields(output_path, names=fields)
    if overflowing:
        listed = "; ".join(
            f"{item['name']} (needs {item['needed_pt']} pt, box {item['box_pt']} pt)"
            for item in overflowing
        )
        message += (
            f"\nWARNING: {len(overflowing)} field value(s) are wider than their box at the form's "
            f"own font, so Chrome, Google Drive and Acrobat cut them off (a pdf_to_image render "
            f"may still show them whole): {listed}. Shorten them, e.g. move the rest to an "
            f"addendum page."
        )
    return message


#: PDF base-14 font → PyMuPDF's short name, for measuring a value at the form's own font.
_BASE14 = {
    ("courier", False): "cour", ("courier", True): "cobo",
    ("times", False): "tiro", ("times", True): "tibo",
    ("helvetica", False): "helv", ("helvetica", True): "hebo",
}


def _measuring_font(font: str) -> str:
    name = (font or "").lower()
    family = ("courier" if "cour" in name or name.startswith("co")
              else "times" if "times" in name or "tiro" in name or "roman" in name
              else "helvetica")
    bold = "bold" in name or name in ("cobo", "hebo", "tibo")
    return _BASE14[(family, bold)]


def overflowing_fields(file_path: str, names=None) -> list[dict]:
    """The filled single-line text fields whose value is wider than their box at the field's own
    font and size — the ones Chrome (PDFium), Drive and Acrobat clip. MuPDF, behind
    ``pdf_to_image``, draws a field in its own narrower font, so a render is no check (CF-040).
    ``names``: only these fields (a full name or its last part); auto-size (0), multi-line and
    comb fields are skipped, since they fit themselves or wrap."""
    wanted = {str(name) for name in names} if names is not None else None
    found = []
    with fitz.open(file_path) as doc:
        for page in doc:
            for widget in page.widgets():
                if widget.field_type != fitz.PDF_WIDGET_TYPE_TEXT:
                    continue
                name = widget.field_name or ""
                if wanted is not None and name not in wanted \
                        and name.rsplit(".", 1)[-1] not in wanted:
                    continue
                value = str(widget.field_value or "")
                size = widget.text_fontsize or 0
                flags = widget.field_flags or 0
                if not value or size <= 0 or flags & (1 << 12) or flags & (1 << 24):
                    continue  # empty, auto-size, multi-line or comb
                needed = fitz.get_text_length(value, fontname=_measuring_font(widget.text_font),
                                              fontsize=size)
                box = widget.rect.width - 4  # the 2 pt inset viewers keep on each side
                if needed > box:
                    found.append({"name": name, "page": page.number + 1,
                                  "needed_pt": round(needed), "box_pt": round(box)})
    return found


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

    # A form's values live in its widgets, and copying pages with show_pdf_page carried page
    # content only, so every value was lost (CF-040). Instead each text field's appearance is drawn
    # anew from its value, then the widgets are baked into the page: the values stay, as page text
    # (searchable), drawn the same in every viewer. Every other field keeps the appearance the form
    # gave it (PyMuPDF cannot redraw a USCIS drop-down: "bad choice field list").
    doc = fitz.open(file_path)
    for page in doc:
        for widget in page.widgets():
            if widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                try:
                    widget.update()
                except Exception:  # noqa: BLE001 — baked with the appearance it has
                    pass
    doc.bake(annots=False, widgets=True)
    doc.save(output_path, garbage=3, deflate=True)
    doc.close()

    return f"Form flattened: {output_path}"


def register(mcp):
    """Register PDF form tools with the MCP server."""
    mcp.tool()(get_form_fields)
    mcp.tool()(fill_form)
    mcp.tool()(flatten_form)
