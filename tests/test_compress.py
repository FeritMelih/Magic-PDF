"""Tests for PDF compression tools."""

import os
import pytest
from magic_pdf.tools.compress import compress_pdf
from magic_pdf.tools.create import get_pdf_info


class TestCompressPdf:
    def test_compress_low(self, sample_pdf, tmp_path):
        output = str(tmp_path / "compressed_low.pdf")
        result = compress_pdf(sample_pdf, level="low", output_path=output)
        assert os.path.isfile(output)
        assert "low" in result
        # Compressed file should still be a valid PDF
        info = get_pdf_info(output)
        assert info["page_count"] == 3

    def test_compress_medium(self, sample_pdf, tmp_path):
        output = str(tmp_path / "compressed_med.pdf")
        result = compress_pdf(sample_pdf, level="medium", output_path=output)
        assert os.path.isfile(output)
        assert "medium" in result

    def test_compress_high(self, sample_pdf, tmp_path):
        output = str(tmp_path / "compressed_high.pdf")
        result = compress_pdf(sample_pdf, level="high", output_path=output)
        assert os.path.isfile(output)
        assert "high" in result

    def test_invalid_level(self, sample_pdf, tmp_path):
        output = str(tmp_path / "bad.pdf")
        with pytest.raises(ValueError):
            compress_pdf(sample_pdf, level="extreme", output_path=output)

    def test_default_output_path(self, sample_pdf):
        result = compress_pdf(sample_pdf, level="low")
        expected = sample_pdf.replace(".pdf", "_compressed.pdf")
        assert os.path.isfile(expected)
        # Cleanup
        os.remove(expected)
