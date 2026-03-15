"""Tests for format conversion tools."""

import os
from unittest.mock import patch

import pytest
from magic_pdf.tools.convert import (
    _find_libreoffice,
    docx_to_pdf,
    image_to_pdf,
    html_to_pdf,
    excel_to_pdf,
    powerpoint_to_pdf,
    pdf_to_image,
)
from magic_pdf.tools.create import get_pdf_info
from magic_pdf.tools.convert import _find_libreoffice as _find_lo

requires_libreoffice = pytest.mark.skipif(
    _find_lo() is None,
    reason="LibreOffice is not installed",
)


class TestImageToPdf:
    def test_single_image(self, sample_image, tmp_path):
        output = str(tmp_path / "from_image.pdf")
        result = image_to_pdf([sample_image], output)
        assert os.path.isfile(output)
        info = get_pdf_info(output)
        assert info["page_count"] == 1

    def test_multiple_images(self, tmp_path):
        from PIL import Image

        images = []
        for i in range(3):
            path = str(tmp_path / f"img{i}.png")
            img = Image.new("RGB", (100, 100), color=(i * 80, 0, 0))
            img.save(path)
            img.close()
            images.append(path)

        output = str(tmp_path / "multi_image.pdf")
        result = image_to_pdf(images, output)
        assert os.path.isfile(output)

    def test_no_images(self, tmp_path):
        output = str(tmp_path / "empty.pdf")
        with pytest.raises(ValueError):
            image_to_pdf([], output)

    def test_invalid_extension(self, tmp_path):
        bad_file = str(tmp_path / "test.xyz")
        with open(bad_file, "w") as f:
            f.write("not an image")
        output = str(tmp_path / "bad.pdf")
        with pytest.raises(ValueError):
            image_to_pdf([bad_file], output)


class TestHtmlToPdf:
    def test_html_string(self, tmp_path):
        output = str(tmp_path / "from_html.pdf")
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        result = html_to_pdf(html, output)
        assert os.path.isfile(output)

    def test_minimal_html(self, tmp_path):
        output = str(tmp_path / "minimal.pdf")
        html = "<p>Simple paragraph</p>"
        result = html_to_pdf(html, output)
        assert os.path.isfile(output)


class TestDocxToPdf:
    def test_convert(self, sample_docx, tmp_path):
        output = str(tmp_path / "from_docx.pdf")
        result = docx_to_pdf(sample_docx, output)
        assert os.path.isfile(output)
        info = get_pdf_info(output)
        assert info["page_count"] >= 1

    def test_invalid_extension(self, tmp_path):
        bad_file = str(tmp_path / "test.txt")
        with open(bad_file, "w") as f:
            f.write("not a docx")
        with pytest.raises(ValueError):
            docx_to_pdf(bad_file)


class TestExcelToPdf:
    def test_convert(self, sample_xlsx, tmp_path):
        output = str(tmp_path / "from_excel.pdf")
        result = excel_to_pdf(sample_xlsx, output)
        assert os.path.isfile(output)
        info = get_pdf_info(output)
        assert info["page_count"] >= 1


class TestPowerpointToPdf:
    def test_convert(self, sample_pptx, tmp_path):
        output = str(tmp_path / "from_pptx.pdf")
        result = powerpoint_to_pdf(sample_pptx, output)
        assert os.path.isfile(output)


class TestPdfToImage:
    def test_all_pages(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "images")
        os.makedirs(output_dir)
        result = pdf_to_image(sample_pdf, output_dir)
        assert "3 page" in result
        images = [f for f in os.listdir(output_dir) if f.endswith(".png")]
        assert len(images) == 3

    def test_single_page(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "single")
        os.makedirs(output_dir)
        result = pdf_to_image(sample_pdf, output_dir, pages="2")
        assert "1 page" in result

    def test_page_range(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "range")
        os.makedirs(output_dir)
        result = pdf_to_image(sample_pdf, output_dir, pages="1-2")
        assert "2 page" in result

    def test_jpeg_format(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "jpeg")
        os.makedirs(output_dir)
        result = pdf_to_image(sample_pdf, output_dir, output_format="jpeg")
        images = [f for f in os.listdir(output_dir) if f.endswith(".jpg")]
        assert len(images) == 3

    def test_invalid_page(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "bad")
        os.makedirs(output_dir)
        with pytest.raises(ValueError):
            pdf_to_image(sample_pdf, output_dir, pages="99")


@pytest.mark.libreoffice
@requires_libreoffice
class TestLibreOfficeConversion:
    """Tests that verify the LibreOffice conversion path."""

    def test_find_libreoffice_returns_path(self):
        path = _find_libreoffice()
        assert path is not None
        assert os.path.isfile(path)

    def test_docx_uses_libreoffice(self, sample_docx, tmp_path):
        output = str(tmp_path / "lo_docx.pdf")
        result = docx_to_pdf(sample_docx, output)
        assert "LibreOffice" in result
        assert os.path.isfile(output)

    def test_excel_uses_libreoffice(self, sample_xlsx, tmp_path):
        output = str(tmp_path / "lo_excel.pdf")
        result = excel_to_pdf(sample_xlsx, output)
        assert "LibreOffice" in result
        assert os.path.isfile(output)

    def test_pptx_uses_libreoffice(self, sample_pptx, tmp_path):
        output = str(tmp_path / "lo_pptx.pdf")
        result = powerpoint_to_pdf(sample_pptx, output)
        assert "LibreOffice" in result
        assert os.path.isfile(output)


class TestFallbackConversion:
    """Tests that verify the pure-Python fallback path (LibreOffice patched out)."""

    def test_docx_fallback(self, sample_docx, tmp_path):
        output = str(tmp_path / "fb_docx.pdf")
        with patch("magic_pdf.tools.convert._find_libreoffice", return_value=None):
            result = docx_to_pdf(sample_docx, output)
        assert "fallback" in result
        assert os.path.isfile(output)

    def test_excel_fallback(self, sample_xlsx, tmp_path):
        output = str(tmp_path / "fb_excel.pdf")
        with patch("magic_pdf.tools.convert._find_libreoffice", return_value=None):
            result = excel_to_pdf(sample_xlsx, output)
        assert "fallback" in result
        assert os.path.isfile(output)

    def test_pptx_fallback(self, sample_pptx, tmp_path):
        output = str(tmp_path / "fb_pptx.pdf")
        with patch("magic_pdf.tools.convert._find_libreoffice", return_value=None):
            result = powerpoint_to_pdf(sample_pptx, output)
        assert "fallback" in result
        assert os.path.isfile(output)
