"""Tests for the whole-file PDF check (CF-172 A)."""

import asyncio
import io

import fitz  # PyMuPDF
import pytest
from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

from magic_pdf.tools.check import check_pdf


def _png(colour) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), colour).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def exhibit_pdf(tmp_path):
    """Page 1: a scanned exhibit (a picture, no text). Page 2: the same, whose picture a
    compression broke (it now draws white) under its page stamp. Page 3: one line of text."""
    path = str(tmp_path / "exhibit.pdf")
    c = pdf_canvas.Canvas(path, pagesize=letter)
    c.drawImage(ImageReader(io.BytesIO(_png((90, 90, 90)))), 72, 200, width=468, height=500)
    c.showPage()
    c.drawImage(ImageReader(io.BytesIO(_png((255, 255, 255)))), 72, 200, width=468, height=500)
    c.setFont("Helvetica", 9)
    c.drawString(300, 30, "EXH. M - 264")
    c.showPage()
    c.setFont("Helvetica", 12)
    c.drawString(72, 700, "The quick brown fox jumps over the lazy dog")
    c.showPage()
    c.save()
    return path


def test_a_page_whose_picture_broke_is_near_blank_and_a_line_of_text_is_not(exhibit_pdf):
    result = check_pdf(exhibit_pdf)
    assert result["page_count"] == 3
    assert result["near_blank_pages"] == "2"
    assert result["pages_without_text"] == "1"
    assert result["pages_without_images"] == "3"
    assert result["image_count"] == 2
    assert result["page_sizes"] == {"612x792 pt": 3}
    assert result["annotations"] == {}
    assert result["summary"] == "3 pages, 1 near-blank (2), no annotations"


def test_an_empty_page_and_a_page_number_alone_are_near_blank(tmp_path):
    path = str(tmp_path / "pages.pdf")
    c = pdf_canvas.Canvas(path, pagesize=letter)
    c.showPage()
    c.setFont("Helvetica", 10)
    c.drawString(300, 30, "12")
    c.showPage()
    c.setFont("Helvetica-Bold", 48)
    c.drawString(180, 400, "EXHIBIT M")  # a divider page reads as content
    c.showPage()
    c.save()
    assert check_pdf(path)["near_blank_pages"] == "1-2"


@pytest.fixture
def highlighted_pdf(tmp_path):
    """Letter pages 1-3 and an A4 page 4. Page 1: three yellow highlight annotations. Page 2: one
    highlight and a note (FreeText). Page 3: yellow drawn into the page itself, no annotation.
    Page 4: text."""
    path = str(tmp_path / "plain.pdf")
    c = pdf_canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica", 12)
    for number in range(1, 4):
        c.drawString(72, 700, f"Alpha beta gamma on page {number}")
        c.drawString(72, 680, "Delta epsilon zeta")
        c.drawString(72, 660, "Eta theta iota")
        if number == 3:
            c.setFillColorRGB(1, 1, 0)
            c.rect(72, 500, 200, 20, stroke=0, fill=1)
            c.setFillColorRGB(0, 0, 0)
        c.showPage()
    c.setPageSize(A4)
    c.drawString(72, 700, "An A4 page: alpha beta gamma delta")
    c.drawString(72, 680, "Epsilon zeta eta theta iota kappa")
    c.showPage()
    c.save()

    doc = fitz.open(path)
    for page_index, words in ((0, ("Alpha", "Delta", "Eta")), (1, ("Alpha",))):
        page = doc[page_index]
        for word in words:
            annot = page.add_highlight_annot(page.search_for(word)[0])
            annot.set_colors(stroke=(1, 1, 0))
            annot.update()
    doc[1].add_freetext_annot(fitz.Rect(72, 300, 300, 330), "Check this", fontsize=10)
    out = str(tmp_path / "highlighted.pdf")
    doc.save(out)
    doc.close()
    return out


def test_annotations_are_counted_by_type_with_their_pages(highlighted_pdf):
    result = check_pdf(highlighted_pdf)
    assert result["annotations"] == {
        "Highlight": {"count": 4, "page_count": 2, "pages": "1-2"},
        "FreeText": {"count": 1, "page_count": 1, "pages": "2"},
    }
    assert result["page_sizes"] == {"612x792 pt": 3, "595x842 pt": 1}
    assert result["near_blank_pages"] == ""
    assert result["summary"] == (
        "4 pages, 0 near-blank, 4 Highlight annotations on 2 pages, "
        "1 FreeText annotation on 1 page"
    )
    assert "colour" not in result


def test_a_colour_is_found_where_it_shows_drawn_or_annotated(highlighted_pdf):
    result = check_pdf(highlighted_pdf, colour="#FFFF00")
    assert result["colour"] == {"colour": "#ffff00", "page_count": 3, "pages": "1-3"}
    assert result["summary"].endswith(", #ffff00 shows on 3 pages")
    assert check_pdf(highlighted_pdf, colour="ff0000")["colour"]["pages"] == ""


@pytest.mark.parametrize("bad", ["yellow", "#ffff0", "#gggggg", ""])
def test_a_colour_that_is_not_hex_is_refused(highlighted_pdf, bad):
    with pytest.raises(ValueError):
        check_pdf(highlighted_pdf, colour=bad)


def test_the_check_is_a_tool_of_the_server():
    from magic_pdf.server import mcp

    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    words = " ".join(tools["check_pdf"].description.split())
    assert "EVERY page" in words and "render only the pages it flags" in words
