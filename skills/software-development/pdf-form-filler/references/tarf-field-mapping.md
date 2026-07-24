# TARF Field Mapping Reference

## Form: SC RESOURCE Time Adjustment Request Form (Rev. 8/2023)

Single-page PDF, 612x792 pts. No AcroForm fields — all blanks are underscore chars or thin rects.

## Template Location

The blank PDF is base64-embedded directly inside `tarf_filler.py` as `EMBEDDED_PDF_B64`.
No external file needed. Source original at:
```
C:\Users\kevin\Desktop\Healthcare_SNF_Docs\blank tarf.pdf
```

## Production Artifacts

| Artifact | Path |
|---|---|
| Python script (embedded) | `C:\Users\kevin\Desktop\tarf_filler.py` |
| Standalone exe | `C:\Users\kevin\Desktop\TARFiller.exe` |
| Desktop shortcut | `C:\Users\kevin\Desktop\TARFiller.lnk` |
| Build venv | `C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\var\tarf_venv\Scripts\python.exe` |

## Exe Build Command

```bash
# Standalone exe (PDF embedded in script — no --add-data needed)
"C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\var\tarf_venv\Scripts\python.exe" -m PyInstaller \
  --onefile \
  --name "TARFiller" \
  --distpath "C:/Users/kevin/Desktop" \
  --workpath "C:/Users/kevin/Desktop/tarf_build" \
  --specpath "C:/Users/kevin/Desktop/tarf_build" \
  "C:/Users/kevin/Desktop/tarf_filler.py"
```

The blank PDF is base64-embedded directly in the script (`EMBEDDED_PDF_B64` variable, ~645K chars). No `--add-data` needed — the exe is fully standalone. At runtime, `get_template_path()` decodes to a temp file via `tempfile.mkstemp()`.

## Installer Build Command

Inno Setup 6.7.3 was installed via `winget install --id JRSoftware.InnoSetup --exact --silent`.

Install path (per-user winget install):
```
C:\Users\kevin\AppData\Local\Programs\Inno Setup 6\ISCC.exe
```

Build:
```bash
"C:\Users\kevin\AppData\Local\Programs\Inno Setup 6\ISCC.exe" "C:\Users\kevin\Desktop\installer\TARFiller_installer.iss"
```

The .iss file lives at `C:\Users\kevin\Desktop\installer\TARFiller_installer.iss` and outputs the installer to `C:\Users\kevin\Desktop\installer\TARFiller_Installer.exe`.

## Pre-Printed Content (DO NOT redraw — leave as-is)

Kevin's blank form already includes these. Do NOT draw over them, do NOT white-out:

| Field | Value |
|---|---|
| Employee Name | Kevin Moon |
| Position | SLP |
| Employee ID | 123713644 |
| Missed Punch checkbox | Checked |
| All or Part of a Meal Not Taken checkbox | Checked |
| A.M. Shift checkbox | Pre-printed "x" inside box |
| Employee Signature | Kevin Moon (cursive) |

**A.M. Shift note:** The pre-printed "x" is DESIRED — the user wants A.M. checked by default. Do NOT white-out or redraw it. Remove am_shift from the shift checkbox map entirely. Any white-out attempt will damage the checkbox box border.

## Field Coordinates (PDF point space, 72 dpi)
ALL y values below are PyMuPDF TOP-LEFT baselines. The OLD block in this
file (x~183/310/330..., y~483/509/526...) was tuned for a DIFFERENT
blank and is WRONG for C:\Users\kevin\blank-tarf.pdf — it put the date
in "Comments", times in "Dept Transfer", signature blank. RE-MEASURE any
blank you fill with scripts/measure_pdf_coords.py; never trust inherited coords.

To use the VALIDATED reportlab coords, see `scripts/tarf_range_generator.py`
(TY(top_y) = 792 - top_y). Verified 2026-07-15 values there:
employee_name (169, TY156.1), position (131, TY179.1), employee_id (430, TY179.1),
missed_punch_box (118, TY226.2 - 6), date (180, TY471.6),
am_shift_box (118, TY497.5 - 6), time_in (309, TY497.5),
meal_start (332, TY514.8), meal_end (404.0, TY514.8),  # meal_start x=332 CLEARS the "Meal Period:" label (ends ~326); x=315/329 overlapped it visually
time_out (316.7, TY531.9), hours (364.6, TY549.2),
emp_sig (195, TY665.3), emp_sig_date (427, TY665.3),
sup_name (148, TY690.5), sup_date (429, TY690.5).
(The -6 on checkbox X's puts the X INSIDE the box.)

### Shift Worked Information (critical fields)

| Field | x | y | Format |
|---|---|---|---|
| date_of_adjustment | 183 | 483 | MM/DD/YYYY |
| time_in | 310 | 509 | H:MM AM/PM |
| meal_start | 330 | 526 | H:MM AM/PM |
| meal_end | 407 | 526 | H:MM AM/PM |
| time_out | 320 | 543 | H:MM AM/PM |
| total_hours | 368 | 560 | HH.HH |

### Checkboxes (draw "X" at font_size=14 — skip pre-checked ones)

| Field | x | y | Notes |
|---|---|---|---|
| cb_missed_punch | 95 | 241 | Pre-checked, skip |
| cb_new_hire | 95 | 258 | |
| cb_forgot_punch | 95 | 275 | |
| cb_lost_badge | 95 | 292 | |
| cb_meal_not_taken | 95 | 310 | Pre-checked, skip |
| cb_meeting_training | 95 | 372 | |
| cb_travel_time | 95 | 410 | |
| cb_dept_transfer | 95 | 448 | |
| cb_am_shift | 95 | 506 | Pre-printed, do NOT touch |
| cb_pm_shift | 95 | 524 | |
| cb_night_shift | 95 | 542 | |

### Comment / Text Lines

| Field | x | y | Notes |
|---|---|---|---|
| site_name | 250 | 83 | Header; white-out pad_t=30 font_size=14 |
| comments_meal | 186 | 333 | |
| comments_meeting | 186 | 371 | |
| comments_travel | 186 | 409 | |
| dept_from | 270 | 428 | |
| dept_to | 408 | 428 | |
| supervisor | 150 | 703 | |
| supervisor_date | 432 | 703 | |

### Signature Fields

| Field | x | y | Notes |
|---|---|---|---|
| employee_signature | 195 | 678 | Pre-printed, skip |
| employee_date | 430 | 678 | Leave blank intentionally |
| supervisor | 150 | 703 | |
| supervisor_date | 432 | 703 | |

## Shift Auto-Detection

A.M. Shift is pre-printed — never auto-detect it. Only select:

| Hour Range | Shift |
|---|---|
| 12-17 | pm_shift |
| 18-23 or 0-5 | night_shift |

## Random 8hr Shift Generator (exact-8h + lunch-before-8h rule)

```python
# total = exactly 8.00 work hours; meal break BEFORE the 8h completes
total_work = 480
first = random.choice([240, 270, 300, 310, 330])   # morning segment <= 5.5h
meal_start = time_in + first
meal_dur = random.choice([30, 60])
meal_end = meal_start + meal_dur
second = total_work - first
time_out = meal_end + second
# since first <= 330 < 480, the meal always starts before the 8h mark.
# AM-shift constraint (this user): time_in in {360,390,420,450,480} (6-8 AM),
# time_out <= 5:00 PM.
```

## Approach #2 — reportlab overlay + pypdf merge (VALIDATED stack)
The bulk `scripts/tarf_range_generator.py` (and the session's `generate_it_tarf.py`)
use `reportlab.pdfgen.canvas.Canvas` to draw an overlay PDF of just the
filled text, then `pypdf.PdfReader` + `template_page.merge_page(overlay_page)`
to merge onto the blank. This is clean (no white-out, no font-embedding issues).
**Coordinates are in reportlab/letter space (PAGE_HEIGHT=792), NOT the
PyMuPDF coords listed elsewhere in this file.** Do NOT mix the two systems.

PITFALL (2026-07-15): the prior `fill_tarf.py` used a coord block tuned for a
DIFFERENT blank — it silently landed every field in the wrong box. The
VALIDATED coords live in `scripts/tarf_range_generator.py` (derived via
`scripts/measure_pdf_coords.py` from the real `C:\Users\kevin\blank-tarf.pdf`).
Run with the `python` interpreter (python3 is a Windows Store stub here):
  python tarf_range_generator.py --start 2026-07-05 --end 2026-07-15 --facility "IT Dept"

## Facilities List

Used in interactive mode via numbered-list picker:

1. Sea Cliff Healthcare
2. Beachside Nursing Center
3. Alamitos West
4. Pacific Coast Therapy
5. IT Department
6. The Hills Post Acute
7. New Orange Hills
8. Mainplace
9. Victoria Healthcare Center
10. Coventry Court
11. St. Elizabeth Healthcare
12. St. Catherine Healthcare
13. Palm Terrace Healthcare Center
+ Custom (type your own, option 0)

## CLI Shortcuts

```
-t / --time-in
-o / --time-out
-m / --meal-start
-e / --meal-end
-d / --date       (REQUIRED, no default)
-s / --site       (default: SC RESOURCE)
--random          (generate 8hr shift)
--supervisor
--reason          (repeatable: new_hire, forgot_punch, lost_badge, meeting_training, travel_time, dept_transfer)
--shift           (repeatable: pm_shift, night_shift)
```
