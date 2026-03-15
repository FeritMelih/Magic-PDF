"""Shared utilities and validation for PDF tools."""

import os
import sys
import logging

logger = logging.getLogger("magic-pdf")

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


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
