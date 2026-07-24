---
name: pdf-form-automation
description: "Analyze and programmatically fill non-interactive PDF forms (no AcroForm fields) using coordinate-based field mapping. Covers form analysis, coordinate extraction, text overlay, and white-out techniques."
version: 1.0.0
author: Hermes Agent
tags: [pdf, forms, automation, pymupdf, pdfplumber, field-mapping]
---

# PDF Form Automation

## Problem
PDF forms often have **no AcroForm fields** — just lines, underscores, and checkboxes drawn as page graphics. A naive sequential fill (field[0]=value, field[1]=value) puts data in the wrong blanks when fields are skipped. For example, a TARF with "Time In → Meal Period start → Meal Period end → Time Out" will put the Time Out value into Meal Period if no lunch is entered.

## Solution
Map fields by **semantic position** (y-coordinate + x-offset) rather than sequential order. Use PyMuPDF (fitz) to overlay text at exact coordinates onto the blank PDF, preserving the original look.

## Tools
| Tool | Install | Purpose |
|---|---|---|
| **PyMuPDF (fitz)** | `pip install pymupdf` | Read & write PDF text overlays at exact coords |
| **pdfplumber** | `pip install pdfplumber` | Extract chars, rects, underscore positions to map fields |

## Workflow

### 1. Analyze the form
```python
import pdfplumber
with pdfplumber.open("form.pdf") as pdf:
    page = pdf.pages[0]
    
    # Find underscore chars → fillable blanks
    for c in page.chars:
        if c["text"] == "_":
            print(f"  underscore: x0={c['x0']:.0f} y_top={c['top']:.0f}")
    
    # Find thin horizontal lines → entry field borders
    for r in page.rects:
        w = r["x1"] - r["x0"]
        h = r["y1"] - r["y0"]
        if h < 3 and w > 50:
            print(f"  line: y={r['y0']:.0f} x0={r['x0']:.0f}-{r['x1']:.0f}")
    
    # Find checkbox-sized squares
    for r in page.rects:
        w = r["x1"] - r["x0"]
        h = r["y1"] - r["y0"]
        if 8 < w < 12 and 8 < h < 12:
            print(f"  checkbox: y={r['y0']:.0f} x0={r['x0']:.0f}")
    
    # Read text near each field to identify labels
    text = page.extract_text()
```

### 2. Map field coordinates
Define a FIELDS dict with (page, x, y) for each form field. Y is the **text baseline** (the top of the underscore line + ~10px for 11pt font).

### 3. Fill the form
```python
import fitz

doc = fitz.open("template.pdf")
page = doc[0]

def draw_text(page, x, y, text, font_size=11, fontname="helv"):
    if not text:
        return
    page.insert_text((x, y), text, fontsize=font_size, fontname=fontname)

# Draw each field
draw_text(page, 310, 509, "1:00 PM")  # Time In
# Skip blank fields — don't draw anything
draw_text(page, 320, 543, "5:00 PM")  # Time Out

doc.save("output.pdf", deflate=True)
```

### 4. Handle checkboxes with white-out
Non-interactive PDFs sometimes have **pre-printed marks** (e.g. "x" already drawn inside a checkbox on the blank template). Always clear the area first:

```python
def draw_checkmark(page, field_x, field_y):
    # White rectangle to clear any pre-printed mark
    page.draw_rect(
        fitz.Rect(field_x - 6, field_y - 14, field_x + 20, field_y + 4),
        color=(1, 1, 1), fill=(1, 1, 1), width=0,
    )
    # Draw our checkmark
    page.insert_text((field_x, field_y), "X", fontsize=14, fontname="helv")
```

## Pitfalls
- **Z-order matters:** draw_rect + insert_text draw ON TOP of the original page content. White rects must be drawn BEFORE checkmarks to clear pre-printed content. Draw all white rects first, then all checkmarks.
- **PDF coordinates:** Origin is bottom-left. pdfplumber reports `top` (distance from page top). Convert to fitz baseline: `baseline_y = page_height - field_top + font_ascent` or just use pdfplumber's `top` directly if it matches.
- **Text grouping:** PyMuPDF's `page.get_text("blocks")` groups nearby text. For verification, sort blocks by y-position. For individual char positions, use `page.get_text("rawdict")`.
- **Font choice:** `"helv"` is Helvetica (built-in, no embedding needed). `"courier"` for monospace. Custom fonts need to be registered.
- **Non-AcroForm PDFs cannot be tab-filled:** Since there are no interactive fields, you're overlaying graphics, not setting field values. The output is a flat PDF. If you need editable fields, use a different approach (create AcroForm or fill with OCR).
- **Multiple pages:** Always check `len(doc)` and iterate if form is multi-page.

## Verification
```python
doc = fitz.open("output.pdf")
page = doc[0]
blocks = page.get_text("blocks")
blocks.sort(key=lambda b: b[1])  # sort by y
for x, y, x1, y1, text, _, _ in blocks:
    print(f"y={y:.0f} x={x:.0f}: {text.strip()}")
```

Or convert to image for visual check:
```python
pix = page.get_pixmap(dpi=200)
pix.save("preview.png")
```

## When to Use
- **Non-interactive PDFs** (lines/underscores, no clickable fields)
- **Forms with conditional fields** where some blanks must stay empty
- **Batch form filling** from a data source (CSV, spreadsheet)
- **TARF forms, evaluation forms, waivers, consent forms**

## When NOT to Use
- PDFs with real AcroForm fields → use `fillpdf` or PyMuPDF's field-setting API
- Fillable web forms → use Playwright or browser tools
- Scanned images (no text layer) → OCR first, then overlay

## Reference Files
- `references/tarf-field-coordinates.md` — Complete coordinate map for the SC RESOURCE TARF form (Rev. 8/2023), including shift auto-detection logic and the sequential-fill bug fix.
