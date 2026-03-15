# Magic-PDF MCP Server — Bug Report

**Date:** 2026-03-15
**Tester:** Claude Code (automated MCP integration tests)
**Server Version:** 0.1.0

## Test Summary

| # | Tool | Status | Notes |
|---|------|--------|-------|
| 1 | `create_pdf_from_text` | PASS | Markdown headings, bold, lists all render correctly |
| 2 | `read_pdf` | PASS | Full read + page range both work |
| 3 | `get_pdf_info` | PASS | Page count, dimensions, properties all correct |
| 4 | `search_pdf` | PASS | Finds matches, returns context snippets, handles not-found |
| 5 | `compress_pdf` | PASS | All 3 levels work (low: 8%, high: 34.8% reduction on text-only PDF) |
| 6 | `merge_pdfs` | PASS | Correctly merges 2 PDFs into 2-page output |
| 7 | `split_pdf` | PASS | Single-range split works |
| 8 | `add_pages` | PASS | Inserts pages at specified position |
| 9 | `remove_pages` | PASS | Removes specified pages |
| 10 | `move_pages` | PASS | Reorders pages correctly |
| 11 | `separate_pages` | PASS | Extracts specified pages into new PDF |
| 12 | `add_header_footer` | FIXED | BUG-001 fixed — non-Latin-1 chars now auto-substituted |
| 13 | `redact_pdf` (text) | PASS | Removes matched text, verified via read_pdf |
| 14 | `redact_pdf` (area) | PASS | Area-based redaction applied |
| 15 | `redact_pdf` (regex) | FIXED | BUG-002 fixed — regex now redacts matched words only |
| 16 | `get_form_fields` | PASS | Detects fields with names, types, values |
| 17 | `fill_form` | PASS | Fills fields, values confirmed via get_form_fields |
| 18 | `flatten_form` | PASS | Produces static PDF |
| 19 | `docx_to_pdf` | PASS | Fallback mode works, text preserved |
| 20 | `image_to_pdf` | PASS | Multi-image PDF created correctly |
| 21 | `html_to_pdf` | PASS | HTML string converted, text readable in output |
| 22 | `excel_to_pdf` | PASS | Fallback mode works, cell data preserved |
| 23 | `powerpoint_to_pdf` | PASS | Fallback mode works |
| 24 | `pdf_to_image` | PASS | PNG and JPEG output, single page and all-pages modes |

### Error Handling (all PASS)

| Test Case | Expected | Actual |
|-----------|----------|--------|
| Read nonexistent file | FileNotFoundError | `File not found: ...` |
| Invalid compression level | ValueError | `Invalid compression level: extreme...` |
| Merge single file | ValueError | `At least 2 PDF files are required` |
| Wrong file extension (docx_to_pdf on .png) | ValueError | `Unsupported file type '.png'` |
| Remove all pages from 1-page PDF | ValueError | `Cannot remove all pages` |
| Read out-of-range pages | ValueError | `Invalid page range: 5-10 (PDF has 1 pages)` |

---

## Bugs

### BUG-001: `add_header_footer` — Non-ASCII characters render as `?` — FIXED

**Severity:** Low
**Tool:** `add_header_footer`
**Steps to reproduce:**
1. Add a footer with an em dash: `Page {page_number} of {total_pages} — {date}`
2. Read the output PDF

**Expected:** Footer text reads `Page 1 of 1 -- 2026-03-15` (em dash substituted to ASCII)
**Original bug:** Footer text read `Page 1 of 1 ? 2026-03-15`

**Root cause:** PyMuPDF's `insert_textbox()` with the built-in `helv` font does not support characters outside the Latin-1 range. The em dash (U+2014) is not in the font's encoding and got replaced with `?`.

**Fix applied:** Added `_sanitize_for_latin1()` function in `modify.py` that auto-substitutes common non-Latin-1 characters before text insertion (e.g., `—` → `--`, smart quotes → straight quotes, `…` → `...`). Characters with no known substitution fall back to `?`.

**Verification:** Direct Python test confirms `Page 1 of 1 — 2026-03-15` → `Page 1 of 1 -- 2026-03-15`

---

### BUG-002: `redact_pdf` (regex mode) — Redacts entire text span instead of matched text only — FIXED

**Severity:** Medium
**Tool:** `redact_pdf` with `use_regex=True`
**Steps to reproduce:**
1. Create a PDF containing: `The quick brown fox jumps over the lazy dog. Python programming is great.`
2. Run `redact_pdf` with `search_text="fox|dog"` and `use_regex=True`
3. Read the output PDF

**Expected:** Only the words "fox" and "dog" are blacked out; surrounding text remains.
**Original bug:** The entire line was removed. Only 1 redaction reported instead of 2.

**Root cause:** The regex redaction code in `modify.py` operated at the text **span** level. When `re.search()` matched anywhere within a span, the entire span's bounding box (`span["bbox"]`) was redacted.

**Fix applied:** Replaced span-level regex matching with a two-step approach:
1. Use `re.finditer()` on full page text to find all regex matches
2. Use `page.search_for(matched_text)` for each unique match to get precise character-level bounding rects

**Verification:** Direct Python test confirms:
- Input: `The quick brown fox jumps over the lazy dog. Python programming is great.`
- Regex: `fox|dog`
- Result: `Applied 2 redaction(s)` — remaining text: `The quick brown  jumps over the lazy . Python programming is great.`

---

## Notes

- All office conversions (DOCX, XLSX, PPTX) used the **pure Python fallback** path since LibreOffice is not installed. Conversion was functional but fidelity is reduced (no complex formatting, images, or styling preserved).
- Compression on a text-only PDF showed 8%–35% reduction. Larger gains expected on image-heavy PDFs.
- The `split_pdf` with `["individual"]` mode was tested via unit tests (passed) but not via MCP in this run.
