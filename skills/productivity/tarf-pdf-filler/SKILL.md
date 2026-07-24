---
name: tarf-pdf-filler
description: Fill the SC-Resource "Time Adjustment Request Form" (TARF) PDF given an employee template + a list of dates/times/breaks. Use when the user wants to generate TARF time-adjustment forms from a blank template, batch-create dated TARFs, swap the SC RESOURCE / IT Dept facility header, or bake employee identity into a reusable template. Handles missed-punch, shift checks, meal/break windows, and supervisor-blank rules.
---

# TARF PDF Filler

Fills the SC-Resource "Time Adjustment Request Form" (a one-page timecard
correction form). Two modes: build a clean base template (employee identity
baked in, facility header blank) and fill entries from JSON.

## Why it exists
The form's facility title ("SC RESOURCE" / "IT Dept") is baked into the PDF
text layer and cannot simply be overlaid — it must be white-boxed out, then
the desired facility name stamped over the blank band. Field coordinates were
measured from `blank-tarf.pdf` (LETTER 612x792, reportlab bottom-left origin)
and visually verified. THIS IS AUTHORITATIVE GEOMETRY — do not reuse coordinates
from any other script; earlier versions used wrong values and were misaligned.

## Prereqs
- `python` (NOT `python3` — the `python3` alias is a broken Store stub on this
  machine). Base interpreter is 3.11.13.
- `pypdf` + `reportlab` must be installed:
  `python -m pip install --user pypdf reportlab`

## Files
- Template source (the blank form with SC RESOURCE baked in): `C:\Users\kevin\blank-tarf.pdf`
- Generated base template (name/ID/role baked, facility header blank):
  `C:\Users\kevin\TARF_template.pdf`
- Generator script: `C:\Users\kevin\tarf_fill.py`

## Usage

### 1. Build the clean base template
```bash
cd /c/Users/kevin
python tarf_fill.py template --out "C:\Users\kevin\TARF_template.pdf"
# optional facility at top (else left blank):
python tarf_fill.py template --out "C:\Users\kevin\TARF_template.pdf" --facility "IT Dept"
```
Employee defaults are Kevin Moon / SLP / 123713644; override with
`--name / --position / --id`. No `--facility` = blank title band (the safe
"template" form the user wants).

### 2. Fill entries from JSON
```bash
cd /c/Users/kevin
python tarf_fill.py fill \
  --template "C:\Users\kevin\TARF_template.pdf" \
  --json entries.json \
  --outdir "C:\Users\kevin\TARF_IT_Jul5-15"
```
`entries.json` is a LIST of objects:
```json
[
  {
    "date": "07/15/2026",
    "shift": "AM",                      // AM | PM | Night
    "reasons": ["Missed Punch"],        // any of: Missed Punch, New Hire,
                                        // Forgot to punch, Lost Badge, Meal Not Taken
    "facility": "IT Dept",              // optional; stamped at top
    "time_in": "7:30 AM",
    "meal_start": "12:00 PM",
    "meal_end": "12:30 PM",
    "time_out": "4:00 PM",
    "hours": "8.00",                    // OPTIONAL — auto-computed if omitted
    "employee_sign": "/s/ Kevin Moon",  // optional; defaults to /s/ <name>
    "employee_sign_date": "07/15/2026", // optional; defaults to date
    "supervisor": "",                   // leave "" for blank (default)
    "supervisor_date": ""               // leave "" for blank (default)
  }
]
```
- `hours` is auto-computed as `(meal_start - time_in) + (time_out - meal_end)`
  in decimal when omitted — verify it equals the intended total.
- Output filename: `TARF <MM-DD-YYYY>.pdf`.

## Verified field coordinates (reportlab x,y, bottom-left)
Copied verbatim from the working script — DO NOT re-derive blindly:
```
employee_name (172,630)  position (130,607)  employee_id (432,607)
missed_punch (93,557)    new_hire (93,539)    forgot (93,520)  lost_badge (93,501)  meal_not (93,482)
date (185,315)
am_shift (93,287)  pm_shift (93,269)  night_shift (93,252)
time_in (315,287)  meal_start (332,270)  meal_end (410,270)  time_out (320,253)  hours (370,235)
emp_sig (200,120)  emp_sig_date (432,120)  sup_name (200,95)  sup_date (432,95)
HEADER white-out rect: (232,702,126,30)   facility stamp centred at (295,715)
```

## Pitfalls
- The underlying template text stream for "SC RESOURCE" survives in the PDF
  even after white-out. A text-extraction tool will STILL list it — that is
  expected and INVISIBLE on render. Verify with a rendered image (PyMuPDF
  `page.get_pixmap`), not `extract_text`.
- `python3` is broken here. Use `python`.
- pypdf `PdfWriter().add_page(pg).write(...)` is NOT valid — `write` is on the
  writer object: `w=PdfWriter(); w.add_page(pg); w.write(open(path,'wb'))`.
- Never reuse coordinates from the old `fill_tarf.py` — they were tuned for a
  different template and produced misalignment (date landing in Travel Time,
  signature empty, etc.).

## Visual verification recipe
```bash
python -c "
import fitz
pg=fitz.open('TARF IT/...pdf')[0]
pg.get_pixmap(dpi=200, clip=fitz.Rect(0,0,pg.rect.width,pg.rect.height*0.30)).save('/tmp/top.png')
"
```
Then vision-inspect `/tmp/top.png` for: no SC RESOURCE, facility stamped,
identity present, alignment correct.
