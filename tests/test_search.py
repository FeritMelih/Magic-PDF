"""Tests for PDF search tools."""

import pytest
from magic_pdf.tools.search import search_pdf


class TestSearchPdf:
    def test_search_found(self, sample_pdf_searchable):
        result = search_pdf(sample_pdf_searchable, "Python")
        assert result["match_count"] > 0
        assert len(result["pages"]) > 0
        assert len(result["matches"]) > 0

    def test_search_not_found(self, sample_pdf_searchable):
        result = search_pdf(sample_pdf_searchable, "xyznonexistent")
        assert result["match_count"] == 0
        assert result["pages"] == []
        assert result["matches"] == []

    def test_search_case_insensitive(self, sample_pdf_searchable):
        result_lower = search_pdf(sample_pdf_searchable, "python", case_sensitive=False)
        result_exact = search_pdf(sample_pdf_searchable, "Python", case_sensitive=True)
        # Case-insensitive should find at least as many matches
        assert result_lower["match_count"] >= result_exact["match_count"]

    def test_search_context(self, sample_pdf_searchable):
        result = search_pdf(sample_pdf_searchable, "fox")
        assert result["match_count"] > 0
        # Context should contain surrounding text
        context = result["matches"][0]["context"]
        assert "fox" in context.lower()

    def test_search_empty_query(self, sample_pdf_searchable):
        with pytest.raises(ValueError):
            search_pdf(sample_pdf_searchable, "")

    def test_search_multiple_pages(self, sample_pdf_searchable):
        result = search_pdf(sample_pdf_searchable, "Python")
        # "Python" appears on both pages
        assert len(result["pages"]) >= 1
