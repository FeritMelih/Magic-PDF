"""PDF compression tools."""

import io
import os

import fitz  # PyMuPDF
from PIL import Image

from .utils import (
    validate_pdf_file,
    validate_file_size,
    generate_output_path,
    ensure_output_dir,
    logger,
)


def _downsample_images(doc: fitz.Document, target_dpi: int, quality: int) -> int:
    """Downsample images in a PDF document. Returns count of processed images."""
    processed_xrefs = set()
    count = 0

    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in processed_xrefs:
                continue
            processed_xrefs.add(xref)

            try:
                base = doc.extract_image(xref)
                if not base:
                    continue

                # Skip small images
                if base["width"] < 100 or base["height"] < 100:
                    continue

                img = Image.open(io.BytesIO(base["image"]))

                # Calculate scale factor (assume source is ~300 DPI)
                scale = target_dpi / 300.0
                if scale >= 1.0:
                    continue

                new_w = max(int(img.width * scale), 50)
                new_h = max(int(img.height * scale), 50)
                img = img.resize((new_w, new_h), Image.LANCZOS)

                buf = io.BytesIO()
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=quality, optimize=True)
                img.close()

                page.replace_image(xref, stream=buf.getvalue())
                count += 1
            except Exception as e:
                logger.debug(f"Could not process image xref {xref}: {e}")
                continue

    return count


def compress_pdf(
    file_path: str,
    level: str = "medium",
    output_path: str | None = None,
) -> str:
    """Compress a PDF with named compression levels.

    Args:
        file_path: Absolute path to the PDF file
        level: Compression level - 'low', 'medium', or 'high'
            - low: Lossless compression, remove duplicate objects/streams. Minimal quality loss.
            - medium: Downsample images to 150 DPI, compress streams. Good balance.
            - high: Downsample images to 72 DPI, strip metadata, aggressive compression. Smallest file.
        output_path: Optional output path (default: same directory with _compressed suffix)
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)

    if level not in ("low", "medium", "high"):
        raise ValueError(f"Invalid compression level: {level}. Use 'low', 'medium', or 'high'.")

    if output_path is None:
        output_path = generate_output_path(file_path, "compressed")
    ensure_output_dir(output_path)

    original_size = os.path.getsize(file_path)
    doc = fitz.open(file_path)

    images_processed = 0

    if level == "low":
        # Lossless: just garbage collect and deflate
        doc.save(output_path, garbage=2, deflate=True)

    elif level == "medium":
        # Downsample images to 150 DPI
        images_processed = _downsample_images(doc, target_dpi=150, quality=75)
        doc.save(output_path, garbage=3, deflate=True, clean=True)

    elif level == "high":
        # Aggressive: downsample to 72 DPI, strip metadata
        images_processed = _downsample_images(doc, target_dpi=72, quality=50)
        doc.set_metadata({})
        doc.save(output_path, garbage=4, deflate=True, clean=True)

    doc.close()

    new_size = os.path.getsize(output_path)
    reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0

    return (
        f"Compressed ({level}): {output_path}\n"
        f"Original: {original_size / 1024:.1f} KB → "
        f"Compressed: {new_size / 1024:.1f} KB "
        f"({reduction:.1f}% reduction, {images_processed} images processed)"
    )


def register(mcp):
    """Register compression tools with the MCP server."""
    mcp.tool()(compress_pdf)
