"""A whole-file PDF check: every page as its reader sees it, without page images (CF-172 A)."""

import fitz  # PyMuPDF
from PIL import Image, ImageChops

from .utils import validate_pdf_file, validate_file_size

# Pages are rendered this small: enough to measure ink and find a colour, about a millisecond a page.
_DPI = 24
# A page with less ink than this share of its area holds at most a page number or a stamp or two
# (one line of 12 pt text is about 0.11%, a full page of text about 7%).
_NEAR_BLANK_INK_PERCENT = 0.05
# A pixel within this much of the asked colour, on each of R, G and B, has that colour.
_COLOUR_TOLERANCE = 48
# A page shows the colour when at least this many of its pixels have it.
_COLOUR_MIN_PIXELS = 3


def _ranges(pages: list[int]) -> str:
    """[1, 2, 3, 7] -> "1-3, 7"."""
    spans: list[list[int]] = []
    for page in pages:
        if spans and page == spans[-1][1] + 1:
            spans[-1][1] = page
        else:
            spans.append([page, page])
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in spans)


def _rgb(colour: str) -> tuple[int, int, int]:
    value = colour.strip().removeprefix("#")
    try:
        if len(value) != 6:
            raise ValueError
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"Not a hex colour: {colour!r} (use e.g. '#ffff00')") from None


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


def check_pdf(file_path: str, colour: str | None = None) -> dict:
    """Check EVERY page of a PDF in one call, as its reader will see it, with no page images:
    cheap enough for a file of 500+ pages. Use it after you build, merge, compress, highlight,
    redact or replace a PDF, on the file the reader gets (a file you uploaded: download it back
    and check that copy), then render only the pages it flags.

    Each page is rendered at 24 DPI, with its annotations, to measure its ink: a page with no more
    ink than a page number or a stamp is listed as near-blank (a picture that a compression broke,
    a page left empty). It also lists the pages with no text layer and the pages with no image,
    counts page sizes, counts annotations by type (Highlight, FreeText, Square, ...) with their
    pages, and with `colour` lists the pages where that colour shows, drawn into the page or as an
    annotation (e.g. "#ffff00" for yellow highlighting).

    Args:
        file_path: Absolute path to the PDF file
        colour: Optional hex colour, e.g. "#ffff00": list the pages where it shows

    Returns:
        Dict with a one-line summary ("567 pages, 0 near-blank, 320 Highlight annotations on
        190 pages"), page_count, near_blank_pages, pages_without_text and pages_without_images
        as page ranges ("1-3, 7"), image_count, page_sizes, annotations by type, and with
        `colour` the pages it shows on
    """
    validate_pdf_file(file_path)
    validate_file_size(file_path)
    wanted = _rgb(colour) if colour is not None else None

    near_blank, without_text, without_images, coloured = [], [], [], []
    image_count = 0
    page_sizes: dict[str, int] = {}
    annotated: dict[str, list[int]] = {}  # type -> one page number per annotation

    with fitz.open(file_path) as doc:
        page_count = doc.page_count
        for number, page in enumerate(doc, 1):
            size = f"{round(page.rect.width)}x{round(page.rect.height)} pt"
            page_sizes[size] = page_sizes.get(size, 0) + 1
            if not page.get_text().strip():
                without_text.append(number)
            images = len(page.get_images())
            image_count += images
            if not images:
                without_images.append(number)
            for annot in page.annots():
                annotated.setdefault(annot.type[1], []).append(number)

            pix = page.get_pixmap(dpi=_DPI, colorspace=fitz.csRGB, alpha=False, annots=True)
            picture = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            histogram = picture.convert("L").histogram()
            ink = sum((255 - level) * n for level, n in enumerate(histogram))
            if ink * 100 < _NEAR_BLANK_INK_PERCENT * 255 * pix.width * pix.height:
                near_blank.append(number)
            if wanted is not None:
                masks = [
                    band.point(lambda v, t=target: 255 if abs(v - t) <= _COLOUR_TOLERANCE else 0)
                    for band, target in zip(picture.split(), wanted)
                ]
                hits = ImageChops.multiply(ImageChops.multiply(masks[0], masks[1]), masks[2])
                if hits.histogram()[255] >= _COLOUR_MIN_PIXELS:
                    coloured.append(number)

    annotations = {
        kind: {"count": len(pages), "page_count": len(set(pages)),
               "pages": _ranges(sorted(set(pages)))}
        for kind, pages in sorted(annotated.items(), key=lambda item: -len(item[1]))
    }
    summary = [_plural(page_count, "page"),
               f"{len(near_blank)} near-blank" + (f" ({_ranges(near_blank)})" if near_blank else "")]
    summary += [
        f"{_plural(found['count'], kind + ' annotation')} on {_plural(found['page_count'], 'page')}"
        for kind, found in annotations.items()
    ] or ["no annotations"]
    result = {
        "page_count": page_count,
        "near_blank_pages": _ranges(near_blank),
        "pages_without_text": _ranges(without_text),
        "pages_without_images": _ranges(without_images),
        "image_count": image_count,
        "page_sizes": page_sizes,
        "annotations": annotations,
    }
    if wanted is not None:
        hex_colour = "#{:02x}{:02x}{:02x}".format(*wanted)
        result["colour"] = {"colour": hex_colour, "page_count": len(coloured),
                            "pages": _ranges(coloured)}
        summary.append(f"{hex_colour} shows on {_plural(len(coloured), 'page')}")
    return {"summary": ", ".join(summary), **result}


def register(mcp):
    """Register the check tool with the MCP server."""
    mcp.tool()(check_pdf)
