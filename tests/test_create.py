"""Tests for PDF creation and reading tools."""

import os
import pytest
from magic_pdf.tools.create import read_pdf, get_pdf_info, create_pdf_from_text


class TestReadPdf:
    def test_read_all_pages(self, sample_pdf):
        result = read_pdf(sample_pdf)
        assert "Page 1" in result
        assert "Page 2" in result
        assert "Page 3" in result

    def test_read_page_range(self, sample_pdf):
        result = read_pdf(sample_pdf, start_page=2, end_page=3)
        assert "Page 1" not in result
        assert "Page 2" in result
        assert "Page 3" in result

    def test_read_single_page(self, sample_pdf):
        result = read_pdf(sample_pdf, start_page=1, end_page=1)
        assert "Page 1" in result
        assert "Page 2" not in result

    def test_read_invalid_range(self, sample_pdf):
        with pytest.raises(ValueError):
            read_pdf(sample_pdf, start_page=5, end_page=10)

    def test_read_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            read_pdf("/nonexistent/file.pdf")

    def test_read_non_pdf(self, tmp_path):
        txt_file = str(tmp_path / "test.txt")
        with open(txt_file, "w") as f:
            f.write("not a pdf")
        with pytest.raises(ValueError):
            read_pdf(txt_file)


class TestGetPdfInfo:
    def test_basic_info(self, sample_pdf):
        info = get_pdf_info(sample_pdf)
        assert info["page_count"] == 3
        assert info["file_size_bytes"] > 0
        assert info["file_size_mb"] >= 0
        assert isinstance(info["encrypted"], bool)
        assert not info["encrypted"]

    def test_page_dimensions(self, sample_pdf):
        info = get_pdf_info(sample_pdf)
        assert "page_width_pt" in info
        assert "page_height_pt" in info
        # A4 is approximately 595 x 842 points
        assert abs(info["page_width_pt"] - 595.28) < 1
        assert abs(info["page_height_pt"] - 841.89) < 1


class TestCreatePdfFromText:
    def test_create_plain_text(self, tmp_path):
        output = str(tmp_path / "output.pdf")
        result = create_pdf_from_text("Hello World", output)
        assert os.path.isfile(output)
        assert "PDF created" in result

    def test_create_markdown(self, tmp_path):
        output = str(tmp_path / "markdown.pdf")
        md_text = "# Heading\n\nSome **bold** and *italic* text.\n\n- Item 1\n- Item 2"
        result = create_pdf_from_text(md_text, output)
        assert os.path.isfile(output)

    def test_create_letter_size(self, tmp_path):
        output = str(tmp_path / "letter.pdf")
        create_pdf_from_text("Test", output, page_size="Letter")
        assert os.path.isfile(output)
        # Verify page size
        info = get_pdf_info(output)
        # Letter is 612 x 792 points
        assert abs(info["page_width_pt"] - 612) < 1

    def test_create_custom_margins(self, tmp_path):
        output = str(tmp_path / "margins.pdf")
        create_pdf_from_text(
            "Test", output, margin_top=36, margin_bottom=36,
            margin_left=36, margin_right=36,
        )
        assert os.path.isfile(output)

    def test_roundtrip(self, tmp_path):
        """Create a PDF and read it back."""
        output = str(tmp_path / "roundtrip.pdf")
        create_pdf_from_text("Hello roundtrip test", output)
        text = read_pdf(output)
        assert "Hello roundtrip test" in text
