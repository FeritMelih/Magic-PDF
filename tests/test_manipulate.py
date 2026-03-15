"""Tests for PDF manipulation tools."""

import os
import pytest
from magic_pdf.tools.manipulate import (
    merge_pdfs,
    split_pdf,
    add_pages,
    remove_pages,
    move_pages,
    separate_pages,
)
from magic_pdf.tools.create import get_pdf_info


class TestMergePdfs:
    def test_merge_two(self, sample_pdf_pair, tmp_path):
        output = str(tmp_path / "merged.pdf")
        result = merge_pdfs(sample_pdf_pair, output)
        assert os.path.isfile(output)
        info = get_pdf_info(output)
        assert info["page_count"] == 4  # 2 pages each

    def test_merge_requires_two(self, sample_pdf, tmp_path):
        output = str(tmp_path / "merged.pdf")
        with pytest.raises(ValueError):
            merge_pdfs([sample_pdf], output)


class TestSplitPdf:
    def test_split_by_ranges(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "split")
        os.makedirs(output_dir)
        result = split_pdf(sample_pdf, ["1-2", "3"], output_dir)
        assert "2 files" in result
        # Check files exist
        files = [f for f in os.listdir(output_dir) if f.endswith(".pdf")]
        assert len(files) == 2

    def test_split_individual(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "split_ind")
        os.makedirs(output_dir)
        result = split_pdf(sample_pdf, ["individual"], output_dir)
        assert "3 files" in result

    def test_split_invalid_range(self, sample_pdf, tmp_path):
        output_dir = str(tmp_path / "split_err")
        os.makedirs(output_dir)
        with pytest.raises(ValueError):
            split_pdf(sample_pdf, ["10-20"], output_dir)


class TestAddPages:
    def test_add_at_beginning(self, sample_pdf_pair, tmp_path):
        output = str(tmp_path / "added.pdf")
        result = add_pages(sample_pdf_pair[0], sample_pdf_pair[1], 1, output)
        info = get_pdf_info(output)
        assert info["page_count"] == 4

    def test_add_at_end(self, sample_pdf_pair, tmp_path):
        output = str(tmp_path / "added_end.pdf")
        result = add_pages(sample_pdf_pair[0], sample_pdf_pair[1], 100, output)
        info = get_pdf_info(output)
        assert info["page_count"] == 4


class TestRemovePages:
    def test_remove_one_page(self, sample_pdf, tmp_path):
        output = str(tmp_path / "removed.pdf")
        result = remove_pages(sample_pdf, [2], output)
        info = get_pdf_info(output)
        assert info["page_count"] == 2

    def test_remove_multiple_pages(self, sample_pdf, tmp_path):
        output = str(tmp_path / "removed2.pdf")
        result = remove_pages(sample_pdf, [1, 3], output)
        info = get_pdf_info(output)
        assert info["page_count"] == 1

    def test_cannot_remove_all(self, sample_pdf, tmp_path):
        output = str(tmp_path / "removed_all.pdf")
        with pytest.raises(ValueError):
            remove_pages(sample_pdf, [1, 2, 3], output)

    def test_invalid_page(self, sample_pdf, tmp_path):
        output = str(tmp_path / "removed_bad.pdf")
        with pytest.raises(ValueError):
            remove_pages(sample_pdf, [10], output)


class TestMovePages:
    def test_reverse_order(self, sample_pdf, tmp_path):
        output = str(tmp_path / "moved.pdf")
        result = move_pages(sample_pdf, [3, 2, 1], output)
        info = get_pdf_info(output)
        assert info["page_count"] == 3

    def test_invalid_page(self, sample_pdf, tmp_path):
        output = str(tmp_path / "moved_bad.pdf")
        with pytest.raises(ValueError):
            move_pages(sample_pdf, [1, 2, 99], output)


class TestSeparatePages:
    def test_extract_pages(self, sample_pdf, tmp_path):
        output = str(tmp_path / "separated.pdf")
        result = separate_pages(sample_pdf, [1, 3], output)
        info = get_pdf_info(output)
        assert info["page_count"] == 2

    def test_invalid_page(self, sample_pdf, tmp_path):
        output = str(tmp_path / "sep_bad.pdf")
        with pytest.raises(ValueError):
            separate_pages(sample_pdf, [10], output)
