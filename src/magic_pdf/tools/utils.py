"""Shared utilities and validation for PDF tools."""

import functools
import os
import sys
import logging

logger = logging.getLogger("magic-pdf")

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# The PDF base-14 fonts (Helvetica, Times, Courier) hold Latin-1 only, so Turkish
# (ş ğ ı İ) and Cyrillic letters come out as boxes or "?". Each family is swapped
# for the first Unicode TrueType set found here, in order: Debian's Liberation and
# DejaVu (the runtime box), then the Windows core fonts. Each entry is a path
# pattern and what fills it for the regular, bold, italic and bold-italic files.
_LIBERATION_STYLES = ("Regular", "Bold", "Italic", "BoldItalic")
_DEJAVU_STYLES = ("", "-Bold", "-Oblique", "-BoldOblique")
_WINDOWS_STYLES = ("", "bd", "i", "bi")
_UNICODE_FONT_CANDIDATES = {
    "sans": [
        ("/usr/share/fonts/truetype/liberation/LiberationSans-{}.ttf", _LIBERATION_STYLES),
        ("/usr/share/fonts/truetype/liberation2/LiberationSans-{}.ttf", _LIBERATION_STYLES),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf", _DEJAVU_STYLES),
        ("C:/Windows/Fonts/arial{}.ttf", _WINDOWS_STYLES),
    ],
    "serif": [
        ("/usr/share/fonts/truetype/liberation/LiberationSerif-{}.ttf", _LIBERATION_STYLES),
        ("/usr/share/fonts/truetype/liberation2/LiberationSerif-{}.ttf", _LIBERATION_STYLES),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSerif{}.ttf", ("", "-Bold", "-Italic", "-BoldItalic")),
        ("C:/Windows/Fonts/times{}.ttf", _WINDOWS_STYLES),
    ],
    "mono": [
        ("/usr/share/fonts/truetype/liberation/LiberationMono-{}.ttf", _LIBERATION_STYLES),
        ("/usr/share/fonts/truetype/liberation2/LiberationMono-{}.ttf", _LIBERATION_STYLES),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono{}.ttf", _DEJAVU_STYLES),
        ("C:/Windows/Fonts/cour{}.ttf", _WINDOWS_STYLES),
    ],
}

# reportlab's base-14 names per family: regular, bold, italic, bold-italic.
_BASE14_NAMES = {
    "sans": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"),
    "serif": ("Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"),
    "mono": ("Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique"),
}


def find_unicode_fonts() -> dict[str, tuple[str, str, str, str]]:
    """Return each family's (regular, bold, italic, bold-italic) Unicode TTF paths.

    A missing style falls back to the family's regular file. A family with no
    candidate on disk is left out, with a warning: its text stays base-14.
    """
    found = {}
    for family, candidates in _UNICODE_FONT_CANDIDATES.items():
        for pattern, styles in candidates:
            paths = [pattern.format(style) for style in styles]
            if os.path.isfile(paths[0]):
                found[family] = tuple(p if os.path.isfile(p) else paths[0] for p in paths)
                break
        else:
            logger.warning(
                "No Unicode TrueType %s font found: its text stays in a base-14 font, "
                "which prints only Latin-1 letters.",
                family,
            )
    return found


def reportlab_unicode_fonts() -> dict[str, str]:
    """Register the Unicode TTFs with reportlab; map each base-14 name to its TTF font."""
    substitutes = {}
    for family, paths in find_unicode_fonts().items():
        substitutes.update(zip(_BASE14_NAMES[family], _register_reportlab_family(paths)))
    return substitutes


@functools.cache
def _register_reportlab_family(paths: tuple[str, ...]) -> tuple[str, ...]:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Named after the file: reportlab keeps the first font registered under a name.
    names = tuple("MagicPdf-" + os.path.splitext(os.path.basename(p))[0] for p in paths)
    for name, path in zip(names, paths):
        pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily(
        names[0], normal=names[0], bold=names[1], italic=names[2], boldItalic=names[3]
    )
    return names


def validate_file_exists(file_path: str) -> None:
    """Validate that a file exists and is readable."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"File not readable: {file_path}")


def validate_pdf_file(file_path: str) -> None:
    """Validate that a file exists and is a PDF."""
    validate_file_exists(file_path)
    if not file_path.lower().endswith(".pdf"):
        raise ValueError(f"Not a PDF file: {file_path}")


def validate_file_size(file_path: str, max_size: int = MAX_FILE_SIZE) -> None:
    """Validate that a file is within size limits."""
    size = os.path.getsize(file_path)
    if size > max_size:
        raise ValueError(
            f"File too large: {size / (1024*1024):.1f} MB "
            f"(max: {max_size / (1024*1024):.0f} MB)"
        )


def validate_extension(file_path: str, allowed: list[str]) -> None:
    """Validate file extension against allowed list."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in allowed:
        raise ValueError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed)}"
        )


def generate_output_path(
    input_path: str, suffix: str, extension: str | None = None
) -> str:
    """Generate an output path based on input path with a descriptive suffix."""
    base, ext = os.path.splitext(input_path)
    if extension is None:
        extension = ext
    return f"{base}_{suffix}{extension}"


def ensure_output_dir(output_path: str) -> None:
    """Ensure the output directory exists."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
