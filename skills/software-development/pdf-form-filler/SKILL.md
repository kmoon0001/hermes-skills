---
name: pdf-form-filler
description: Build Python scripts to programmatically fill non-interactive PDF forms (lines/underscores, no AcroFields) with smart field mapping — never misplace data into a wrong blank.
category: software-development
triggers:
  - "fill this PDF form"
  - "automate filling out this PDF"
  - "TARF time adjustment form"
  - "map form fields"
  - "PDF overlay text"
  - "random shift generator"
  - "bulk TARF generation date range"
  - "randomize shifts across a week"
  - "editable header on PDF form"
  - "white-out pre-printed PDF content"
  - "standalone exe"
  - "distribute PDF filler"
  - "pyinstaller embedded PDF"
---

# PDF Form Filler (Non-Interactive / AcroForm-less)

Build Python scripts that overlay text onto static PDF forms at precise coordinates. Handles the common case where the PDF has only drawn lines/underscores rather than proper AcroForm fields.

## The Core Problem: Sequential vs Semantic Mapping

Naive form fillers iterate over blank lines in visual order. When a form has fields arranged:

```
Time In: _____  (field 1)
Meal Period: _____ to _____  (fields 2, 3)
Time Out: _____  (field 4)
```

A sequential fill puts the user's end time into the Meal Period field if no meal is provided. **The fix: map every field by its semantic label / position, not by its index in the field list.**

## Handling Pre-Populated Form Content

Many "blank" forms actually come with pre-printed data — name, employee ID, signature, and pre-checked checkboxes. The script must explicitly skip these:

1. Identify which fields are pre-printed at analysis time (check the PDF's existing text chars)
2. Remove those fields from your drawing calls
3. For pre-checked checkboxes, remove them from the checkbox map so the script never draws over them
4. For pre-printed shift checkboxes (like A.M. Shift), remove from the shift map AND adjust the auto-detection to skip that shift choice

## Global Offset for Alignment

When overlaid text sits slightly off from the blank lines, add global offset constants:

```python
X_OFFSET = 3   # shift right
Y_OFFSET = -3  # shift up (PDF y decreases upward)
```

Apply in draw_text so FIELDS coordinates stay as measured values:

```python
page.insert_text(point=(field["x"] + X_OFFSET, field["y"] + Y_OFFSET), ...)
```

Start with ±3 and adjust based on visual feedback. The offset applies to ALL fields uniformly.

## Workflow

### 1. Analyze the blank PDF

Use `pdfplumber` to extract the form's layout:

```python
import pdfplumber
pdf_path = 'blank_form.pdf'
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    
    # Extract text to identify labels
    text = page.extract_text()
    print(text)
    
    # Find rects (drawn boxes and lines)
    for r in page.rects:
        print(f'  x0={r["x0"]:.0f} y0={r["y0"]:.0f} x1={r["x1"]:.0f} y1={r["y1"]:.0f} w={r["x1"]-r["x0"]:.0f} h={r["y1"]-r["y0"]:.0f}')
    
    # Find underscore chars (fillable blank lines)
    for c in page.chars:
        if c['text'] == '_':
            print(f'  underscore at x0={c["x0"]:.0f} y={c["top"]:.0f}')
    
    # Render for reference
    img = page.to_image(resolution=200)
    img.save('reference.png')
```

Also render a PNG with `vision_analyze` to visually cross-reference field positions.

### 2. Build the field coordinate map

Define every field by its PDF point-space coordinates. `y` is the text **baseline** (slightly below the drawn line):

```python
FIELDS = {
    "field_name": {"page": 0, "x": 310, "y": 509},  # (x, y) = text insertion point
}
```

Text goes at `(x, y)` where `y` is about 10pt below the underscore/line top.

### 3. Overlay text with PyMuPDF (fitz)

```python
import fitz

doc = fitz.open(template_path)
page = doc[0]
page.insert_text(
    point=(x, y),
    text="1:00 PM",
    fontsize=11,
    fontname="helv",        # Helvetica (built-in)
    color=(0, 0, 0),        # black
)
doc.save(output_path, deflate=True)
doc.close()
```

### 4. Handle pre-printed marks (white-out)

If the blank template has pre-printed text that CONFLICTS with your data, draw a white rectangle first:

```python
page.draw_rect(
    fitz.Rect(x - 6, y - 14, x + 20, y + 4),
    color=(1, 1, 1),
    fill=(1, 1, 1),
    width=0,
)
```

**CRITICAL PITFALL — white-out destroys checkbox box borders:**

The default `white_out(pad_l=6, pad_t=14, pad_r=20, pad_b=4)` draws a ~26×18pt white rect. A typical checkbox box is only ~10×10pt. This means the white rect completely covers the box outline, making it disappear.

**NEVER white-out a pre-printed checkbox.** If the user's blank form already has a checkmark (like A.M. Shift with a pre-printed "x"), leave it entirely alone:
- Remove the field from the checkbox/shift drawing map
- Remove it from auto-detection logic
- Do NOT call `draw_checkmark()` on it — that function calls white_out first

If you MUST erase a tiny glyph inside a checkbox (like a stray character), use an EXACT rect that fits inside the box:
```python
page.draw_rect(
    fitz.Rect(90, 495, 101, 505),   # tight to the glyph, INSIDE the box
    color=(1, 1, 1), fill=(1, 1, 1), width=0,
)
```
But even this risks edge overlap at 72dpi. **The safer rule: if the pre-printed mark is wanted, don't touch it.**

**When to LEAVE pre-printed content alone (expanded):**
If the blank form already has content the user wants, do NOT white-out or redraw:
- Pre-checked checkboxes → remove from checkbox map entirely
- Pre-filled employee info → skip drawing calls, don't include in data dict keys
- Pre-printed signature → remove from drawing
- Pre-printed header text → white-out generously (pad_top=30) and draw replacement at font_size=14

This avoids destroying checkbox box borders, creating double-print artifacts, and misaligned overlays.

**Testing white-out visually — text extraction LIES:**
`page.get_text('blocks')` returns pre-printed text even AFTER a white rect covers it. The PDF content stream still contains the original text; the white rect is a separate layer on top that the text extractor ignores.

**ALWAYS use vision_analyze for white-out validation:**
```python
pix = page.get_pixmap(dpi=200)
pix.save('verify.png')
```
Then call `vision_analyze(image_url='verify.png', question='Is the X removed?')`. Never trust text extraction for white-out verification.

### 5. Smart time parsing

Accept multiple time formats. The user should be able to type "1p", "1:00 PM", "13:00", "1 pm" — all should work. Use `datetime.strptime` with a fallback chain.

### 6. Auto-calculate totals

If the form has a "Total Hours" field, compute it from time in/out minus meal. Handle crossing midnight.

## Pitfalls (session-sharpened 2026-07-15)
- **WRONG template = every field in the wrong box.** Inherited coords (even from a "proven" prior script) are only valid for the EXACT blank PDF they were tuned on. This session's `tarf_range_generator.py` shipped coords tuned for a DIFFERENT blank: the date landed in "Comments", times in "Dept Transfer", signature blank. **Fix: re-derive every coordinate from the actual blank you're filling** with `scripts/measure_pdf_coords.py` (PyMuPDF word boxes -> reportlab pts) before trusting any hardcoded map. Never reuse a coord block across templates.
- **BAKED-IN pre-printed header (not a blank).** The SC Resource TARF blanks bake "SC RESOURCE" into the PDF stream. A plain reportlab `drawCentredString` overlay just slaps the new facility name UNDER it — garbled "SC RESOURCE IT Dept" title. **PROVEN FIX (2026-07-15):** draw a WHITE RECTANGLE on the reportlab overlay canvas over the baked text, then draw the replacement title on top, then merge the overlay onto the template with pypdf. The white rect is a real opaque layer, so it reliably hides the baked words:
  ```python
  c.setFillColorRGB(1, 1, 1)
  c.rect(232, 702, 126, 30, fill=1, stroke=0)   # white-out band; reportlab y = 792 - template_pdf_y
  c.setFillColorRGB(0, 0, 0)
  c.setFont("Helvetica-Bold", 13)
  c.drawCentredString(295, 715, "IT Dept")
  ```
  **REDACTION TRAP — do NOT use `add_redact_annot`/`apply_redactions()` for this.** It silently failed this session: even when a "cleaned" template was saved, `main()` re-read the ORIGINAL blank (not the cleaned copy), so the old header reappeared on every output. Redaction also leaves the text in the content stream (text extraction still finds "SC RESOURCE") and can miss glyphs on certain PDFs. The white-rect-on-overlay method above is bulletproof. **VERIFY removal with `vision_analyze` on a rendered PNG — text extraction will STILL list the old header even after a correct white-out, so it can never confirm removal. The user WILL catch a false "done" if the header is still visible.**
- **Checkbox X floats above the box.** reportlab `drawString` at the label's baseline puts the "X" just above the square. **Fix: nudge the checkbox Y down ~6pt** (in reportlab space, that's `-6` since y grows upward). Verified: X then sits inside the box.
- **Supervisor blank means BOTH name and date blank.** A prior run filled the supervisor "Date Signed" with the entry date — wrong when the user said leave supervisor spot blank. Draw only employee sig + employee date; skip sup_name AND sup_date.
- **Value-vs-label horizontal overlap (easy to miss).** When a fillable value sits immediately RIGHT of its label with little/no box gap, the value X must be pushed PAST the label's right edge (measure label x1), NOT just to the box's nominal x0. Confirmed on the TARF meal-period start: label "Meal Period:" ends at x≈326; drawing the value at x=315 (or even x=329, the box left edge) overlapped the label text visually. Only x≈332 cleared it. Rule: value_x = max(box_x0, label_x1 + 4). This is SEPARATE from the checkbox-X vertical float fix.
- **Random 8h shift with "lunch before 8 hours" rule.** When total must be exactly 8.00 work hours AND a meal break before the 8h completes: `total_work=480`, `first = randint(240,330)` (morning segment ≤5.5h), `meal_start = time_in + first`, `meal_dur ∈ {30,60}`, `second = total_work - first`, `time_out = meal_end + second`. Because `first ≤ 330 < 480`, the meal always starts before 8h elapse. Never let `first` approach 480 or lunch lands at/after the 8h mark. AM-shift constraint (this user): `time_in ∈ {360,390,420,450,480}` (6:00–8:00 AM), `time_out ≤ 5:00 PM`.



- **Blank lines vs rects**: Some PDFs use underscore characters (`_`) for blank fields, others use thin horizontal rectangles. Check both `page.chars` (for `_`) and `page.rects` (for thin `h < 3, w > 50` rects).
- **Baseline offset**: PyMuPDF's `insert_text` places the text baseline at `y`. If text appears too high/low, adjust `y` by ±2-3 points.
- **Font size**: Built-in fonts (`helv`, `tiro`, `cour`) are small at `fontsize=11`. For checkbox X marks, use `fontsize=14`.
- **Drawing order**: In PyMuPDF, `draw_rect` then `insert_text` means the text renders ON TOP of the rect. White-out rects must come BEFORE text calls.
- **Non-embedded fonts**: The built-in PDF Base 14 fonts (`helv`=Helvetica, `tiro`=Times, `cour`=Courier) are available everywhere without embedding. Use these.
- **Text block grouping**: `page.get_text('blocks')` may combine nearby text into one block. For precise verification, use `page.get_text('text')` or check raw char positions.
- **venv isolation**: pip may require a virtualenv. Create one with `python -m venv <path>` and activate before installing pymupdf/pdfplumber.
- **Pre-printed form content**: Many "blank" forms already have employee name, ID, signature, and certain checkboxes pre-printed. Check the PDF's text chars at analysis time to identify pre-populated fields. Remove them from drawing calls rather than drawing on top (which creates double-print artifacts).
- **Global alignment offset**: When the initial text overlay is slightly off (common with pre-printed forms), add X_OFFSET/Y_OFFSET constants rather than tweaking every field coordinate. Start with ±3 points and adjust. This keeps the FIELDS map as measured values and the rendering logic separate.
- **Per-field Y override**: When one field (like date) needs different vertical alignment than the rest, add a Y_ADJ dict: `Y_ADJ = {"date_of_adjustment": +5}`. Applied on top of Y_OFFSET in draw_text: `y = field["y"] + Y_OFFSET + Y_ADJ.get(field_name, 0)`. Positive = lower, negative = higher.
- **White-out visual bleed**: `page.get_text('blocks')` still returns pre-printed text even after a white rect covers it. Always use vision_analyze (screenshot) to verify visual appearance — text extraction is misleading here.
- **Editable headers**: To let users change a printed header (e.g., site name), white-out the area generously (pad_top=20-30) then draw the replacement text at font_size=14. White rect must extend ABOVE the text cap height.
- **Random shift generator pattern**: For forms that need test data or convenience filling, add a `--random` flag that generates realistic shifts. For an exact-8h-with-lunch rule see the dedicated pitfall above: `first = randint(240,330)` morning segment, meal after `first`, `second = 480 - first`, so meal always starts before the 8h mark. If no such constraint, simple: start between 8-10am, 30min lunch before the 5-hour mark, end = start + 8.5hrs (8hr work + 0.5hr lunch). Example: `random.randint(8,10)` for hour, `random.choice([0,15,30,45])` for minutes.
- **Date handling**: Never auto-default to today's date — the user's adjustment date is rarely the current day. Make date REQUIRED input, no fallback. Validate format but accept MM/DD/YYYY.

### 7. Facility/Site picker (numbered-list pattern)

When the same form template is used across multiple facilities (e.g., skilled nursing chain), add a numbered-list picker in interactive mode:

```python
FACILITIES = [
    "Sea Cliff Healthcare",
    "Beachside Nursing Center",
    "Alamitos West",
    # ... add all facilities
]

def pick_facility():
    print("\\n[FACILITY]")
    print("  0. Custom (type your own)")
    for i, name in enumerate(FACILITIES, 1):
        print(f"  {i}. {name}")
    while True:
        raw = input("\\n  Pick facility (number or name): ").strip()
        if not raw:
            return ""
        try:
            n = int(raw)
            if n == 0:
                return input("  Enter facility name: ").strip()
            if 1 <= n <= len(FACILITIES):
                return FACILITIES[n - 1]
        except ValueError:
            pass
        # Type partial name
        matches = [f for f in FACILITIES if raw.lower() in f.lower()]
        if len(matches) == 1:
            return matches[0]
        return raw  # treat as custom name
```

The selected facility name replaces the form's static header via white-out + draw_text at the header coordinates.

### Distributing as a Standalone .exe

To package a PDF-filler script as a single distributable .exe using PyInstaller:

**Option A — template alongside (simpler):**

```bash
python -m pip install pyinstaller
python -m PyInstaller --onefile --name "AppName" \
  --distpath "C:/path/to/output" \
  --add-data "path/to/blank template.pdf;." \
  "path/to/script.py"
```

Script needs a `get_template_path()` that checks `sys._MEIPASS` when frozen:

```python
def get_template_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "blank template.pdf")
    return TEMPLATE_PATH
```
Replace all `TEMPLATE_PATH` references with `get_template_path()`.

**Option B — template embedded directly (fully standalone, recommended for distribution):**

Base64-encode the template PDF and embed it as a string variable. No external file needed at runtime — the exe is fully self-contained.

```python
import base64, os, tempfile

EMBEDDED_PDF_B64 = """<base64-encoded PDF content here>"""

def get_template_path():
    """Extract embedded PDF to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, 'wb') as f:
        f.write(base64.b64decode(EMBEDDED_PDF_B64))
    return path
```

To generate the base64 string:

```python
import base64
with open('blank_template.pdf', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
print(f"Length: {len(b64)} chars")  # ~645K for a typical 1-page PDF
```

Paste the output as the `EMBEDDED_PDF_B64` string. Then build WITHOUT `--add-data`:

```bash
python -m PyInstaller --onefile --name "AppName" "path/to/script.py"
```

**Result:** A ~27MB single .exe that bundles both the Python runtime AND the template PDF. Send the .exe alone — nothing else needed.

**Size note:** PyMuPDF (fitz) is the bulk (~25MB). The embedded PDF adds ~640K of base64 text to the .py file. PyInstaller compresses the final .exe.

**Desktop shortcut (PowerShell):**
```powershell
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut('C:\path\to\AppName.lnk')
$Shortcut.TargetPath = 'C:\path\to\AppName.exe'
$Shortcut.WorkingDirectory = 'C:\path\to\folder'
$Shortcut.Description = 'Description'
$Shortcut.Save()
```

**Custom icon (.ico) creation with Pillow:**
```python
from PIL import Image, ImageDraw, ImageFont
sizes = [256, 128, 64, 48, 32, 16]
img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
# draw on img ...
img.save('app.ico', format='ICO', sizes=[(s, s) for s in sizes])
```

**Windows installer with Inno Setup:**
After installing Inno Setup (via `winget install --id JRSoftware.InnoSetup` or from jrsoftware.org), create an `.iss` file:

```iss
[Setup]
AppName=YourApp
AppVersion=1.0
DefaultDirName={autopf}\YourApp
DefaultGroupName=YourApp
OutputDir=.
OutputBaseFilename=YourApp_Installer
SetupIconFile=..\app.ico

[Files]
Source: "..\YourApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\app.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\YourApp"; Filename: "{app}\YourApp.exe"; \
    WorkingDir: "{app}"; IconFilename: "{app}\app.ico"
Name: "{autoprograms}\YourApp"; Filename: "{app}\YourApp.exe"; \
    WorkingDir: "{app}"; IconFilename: "{app}\app.ico"

[Run]
Filename: "{app}\YourApp.exe"; Flags: postinstall nowait skipifsilent
```

Compile with:
```bash
"path\to\ISCC.exe" "path\to\installer.iss"
```

On Windows (per-user install via winget), ISCC.exe lives at:
```
C:\Users\<user>\AppData\Local\Programs\Inno Setup 6\ISCC.exe
```

**Distribution options summary:**
1. **Script only** — send `.py` file, recipient needs Python + pip install pymupdf
2. **Standalone .exe** (Option B above) — ~27MB, single file, no deps needed    
3. **Installer .exe** — wraps the standalone exe into a proper Windows installer with shortcuts, uninstall support, and icon

Requires PyMuPDF: `C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\var\tarf_venv\Scripts\python.exe`

## Bulk Date-Range Generation
For "make TARFs for every day from X to Y", use `scripts/tarf_range_generator.py`
(reportlab overlay + pypdf merge — the validated stack, NOT the PyMuPDF coords).
One TARF per day with randomized but valid 8h AM shifts, lunch mid-shift,
supervisor blank, employee signed. Run with the `python` interpreter (python3 is a
Windows Store stub on this machine):
python scripts/tarf_range_generator.py --start 2026-07-05 --end 2026-07-15 --facility "IT Dept"

## References
## References
- `references/tarf-field-mapping.md` — Full coordinate map and technique from the TARF filler project
- `scripts/measure_pdf_coords.py` — PyMuPDF recipe to re-derive reportlab-safe coords from ANY blank PDF (never inherit hand-tuned coords)
- `scripts/tarf_range_generator.py` — VALIDATED bulk generator (corrected coords, 2026-07-15). Run with `python` (not python3): `python scripts/tarf_range_generator.py --start 2026-07-05 --end 2026-07-15 --facility "IT Dept"`
- Production script (on Desktop): `C:\Users\kevin\Desktop\tarf_filler.py` — interactive + CLI modes, smart time mapping, meal deduction, white-out handling, total hours auto-calc
  Usage: `python C:\\Users\\kevin\\Desktop\\tarf_filler.py` (interactive)
  Or: `python C:\\Users\\kevin\\Desktop\\tarf_filler.py --time-in "8:00 AM" --time-out "5:00 PM" --date "06/01/2026"`
  Requires PyMuPDF: `C:\\Users\\kevin\\AppData\\Local\\hermes\\profiles\\coding-profile\\var\\tarf_venv\\Scripts\\python.exe`
