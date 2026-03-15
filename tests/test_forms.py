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
