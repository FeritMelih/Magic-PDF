"""Tests for PDF modification tools."""

import os
import pytest
from magic_pdf.tools.modify import add_header_footer, redact_pdf
from magic_pdf.tools.create import read_pdf, get_pdf_info


class TestAddHeaderFooter:
    def test_add_header(self, sample_pdf, tmp_path):
        output = str(tmp_path / "header.pdf")
        result = add_header_footer(sample_pdf, header="Test Header", output_path=output)
        assert os.path.isfile(output)
        assert "header" in result

    def test_add_footer(self, sample_pdf, tmp_path):
        output = str(tmp_path / "footer.pdf")
        result = add_header_footer(sample_pdf, footer="Page {page_number}", output_path=output)
        assert os.path.isfile(output)
        assert "footer" in result

    def test_add_both(self, sample_pdf, tmp_path):
        output = str(tmp_path / "both.pdf")
        result = add_header_footer(
            sample_pdf,
            header="Header",
            footer="Page {page_number} of {total_pages}",
            output_path=output,
        )
        assert os.path.isfile(output)
        assert "header" in result
        assert "footer" in result

    def test_requires_header_or_footer(self, sample_pdf, tmp_path):
        output = str(tmp_path / "none.pdf")
        with pytest.raises(ValueError):
            add_header_footer(sample_pdf, output_path=output)

    def test_page_count_preserved(self, sample_pdf, tmp_path):
        output = str(tmp_path / "preserved.pdf")
        add_header_footer(sample_pdf, header="H", output_path=output)
        info = get_pdf_info(output)
        assert info["page_count"] == 3


class TestRedactPdf:
    def test_text_redaction(self, sample_pdf_searchable, tmp_path):
        output = str(tmp_path / "redacted.pdf")
        result = redact_pdf(
            sample_pdf_searchable, search_text="Python", output_path=output
        )
        assert os.path.isfile(output)
        assert "redaction" in result

        # Verify text is removed
        text = read_pdf(output)
        assert "Python" not in text

    def test_area_redaction(self, sample_pdf, tmp_path):
        output = str(tmp_path / "area_redacted.pdf")
        areas = [{"page": 1, "x": 50, "y": 690, "width": 300, "height": 30}]
        result = redact_pdf(sample_pdf, areas=areas, output_path=output)
        assert os.path.isfile(output)

    def test_requires_text_or_area(self, sample_pdf, tmp_path):
        output = str(tmp_path / "none.pdf")
        with pytest.raises(ValueError):
            redact_pdf(sample_pdf, output_path=output)

    def test_invalid_area_page(self, sample_pdf, tmp_path):
        output = str(tmp_path / "bad_area.pdf")
        areas = [{"page": 99, "x": 0, "y": 0, "width": 100, "height": 100}]
        with pytest.raises(ValueError):
            redact_pdf(sample_pdf, areas=areas, output_path=output)
