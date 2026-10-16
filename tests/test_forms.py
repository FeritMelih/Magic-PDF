"""Tests for PDF form tools."""

import os
import pytest
from magic_pdf.tools.forms import get_form_fields, fill_form, flatten_form
from magic_pdf.tools.create import get_pdf_info


class TestGetFormFields:
    def test_get_fields(self, sample_form_pdf):
        result = get_form_fields(sample_form_pdf)
        assert result["field_count"] >= 2
        field_names = [f["name"] for f in result["fields"]]
        assert "name" in field_names
        assert "email" in field_names

    def test_no_fields(self, sample_pdf):
        result = get_form_fields(sample_pdf)
        assert result["field_count"] == 0


class TestFillForm:
    def test_fill_fields(self, sample_form_pdf, tmp_path):
        output = str(tmp_path / "filled.pdf")
        result = fill_form(
            sample_form_pdf,
            {"name": "John Doe", "email": "john@example.com"},
            output,
        )
        assert os.path.isfile(output)
        assert "Filled" in result

    def test_empty_fields(self, sample_form_pdf, tmp_path):
        output = str(tmp_path / "empty.pdf")
        with pytest.raises(ValueError):
            fill_form(sample_form_pdf, {}, output)


class TestFlattenForm:
    def test_flatten(self, sample_form_pdf, tmp_path):
        output = str(tmp_path / "flattened.pdf")
        result = flatten_form(sample_form_pdf, output)
        assert os.path.isfile(output)
        assert "flattened" in result.lower()
        # Flattened PDF should still have pages
        info = get_pdf_info(output)
        assert info["page_count"] >= 1

    def test_flatten_keeps_the_values_as_page_text(self, sample_form_pdf, tmp_path):
        """CF-040: copying pages dropped the widgets, so every filled value was lost."""
        import fitz

        filled = str(tmp_path / "filled.pdf")
        fill_form(sample_form_pdf, {"name": "John Doe", "email": "john@example.com"}, filled)
        output = str(tmp_path / "flattened.pdf")
        flatten_form(filled, output)
        with fitz.open(output) as doc:
            assert sum(1 for page in doc for _ in page.widgets()) == 0
            text = doc[0].get_text()
        assert "John Doe" in text and "john@example.com" in text


class TestFormFit:
    def test_a_value_wider_than_its_box_is_warned(self, sample_form_pdf, tmp_path):
        """CF-040: a value clipped in Chrome and Drive looked whole in the MuPDF render, so Copilot
        said it fit. fill_form now names it, measured at the field's own font."""
        output = str(tmp_path / "filled.pdf")
        result = fill_form(sample_form_pdf, {"name": "Asylum Applicant/Removal Proceedings " * 2,
                                             "email": "john@example.com"}, output)
        assert "WARNING: 1 field value(s)" in result and "name (needs" in result
        assert "email" not in result.split("WARNING", 1)[1]

    def test_values_that_fit_carry_no_warning(self, sample_form_pdf, tmp_path):
        output = str(tmp_path / "filled.pdf")
        result = fill_form(sample_form_pdf, {"name": "John Doe"}, output)
        assert "WARNING" not in result
