"""
tarf_range_generator.py — bulk TARF timecard generator (SC Resource / IT Dept
Time Adjustment Request Form, Rev. 8/2023).

Fills the NON-interactive blank-tarf.pdf via a reportlab text overlay merged with
pypdf. Generates ONE TARF per day across a date range, with randomized but
VALID 8-hour AM shifts and a lunch break taken mid-shift (before the 8h mark).
Employee signs; supervisor LEFT BLANK.

WHY THIS STACK: reportlab.canvas overlay + pypdf.PdfReader/PdfWriter.merge_page
is a clean alternative to PyMuPDF (fitz). Coordinates below are VALIDATED 2026-07-15
against C:\Users\kevin\blank-tarf.pdf using measure_pdf_coords.py (PyMuPDF word boxes ->
reportlab letter space). The OLD coords in this file (pre-2026-07-15) were tuned for a
DIFFERENT blank and landed every field in the wrong box — do NOT revert to them.

RUN with the `python` interpreter (NOT python3 — that is a Windows Store stub here):
  python tarf_range_generator.py --start 2026-07-05 --end 2026-07-15 --facility "IT Dept"

DEPS: pypdf, reportlab  (install under the `python` venv: python -m pip install pypdf reportlab)

HEADER: the blank template bakes in "SC RESOURCE". To write a different facility,
white-out the "SC RESOURCE" words in the template with fitz.redact + apply_redactions,
then insert_text the new title BEFORE the pypdf merge loop (see generate_it_tarf.py).
"""
import os, random, argparse
from datetime import date, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

TEMPLATE_PDF = r"C:\Users\kevin\blank-tarf.pdf"

# Employee config — prefilled (matches proven fill_tarf.py)
EMPLOYEE_NAME = "Kevin Moon"
POSITION = "SLP"
EMP_ID = "123713644"
EMP_SIG = "/s/ Kevin Moon"
SUP_NAME = ""          # supervisor LEFT BLANK per request

PAGE_WIDTH, PAGE_HEIGHT = letter   # 612 x 792, origin BOTTOM-LEFT (reportlab)

# --- COORDINATES VALIDATED 2026-07-15 via measure_pdf_coords.py ---
# Template is 612x792, top-left origin in PyMuPDF; reportlab y = 792 - pymupdf_top_y.
def TY(top_y):
    return PAGE_HEIGHT - top_y

coords = {
    # Employee info (labels: Name y156.1, Position y179.1, ID y179.1)
    "employee_name": (169, TY(156.1)),
    "position":      (131, TY(179.1)),
    "employee_id":   (430, TY(179.1)),
    # Reason: Missed Punch checkbox ~ left of "Missed" (x126, y226)
    "missed_punch_box": (118, TY(226.2) - 6),   # -6 puts X INSIDE the box
    # Shift Worked: Date (label y471.6) ; AM box (x126, y497.5)
    "date":        (180, TY(471.6)),
    "am_shift_box":(118, TY(497.5) - 6),   # -6 puts X INSIDE the box
    "pm_shift_box":(118, TY(514.8)),
    "night_box":   (118, TY(531.9)),
    # Time In box x309 (label y497.5) ; Meal Period boxes x328.9 & 404 (y514.8)
    # Time Out x316.7 (y531.9) ; Total Hours x364.6 (y549.2)
    "time_in":  (309, TY(497.5)),
    "meal_start":(328.9, TY(514.8)),
    "meal_end":  (404.0, TY(514.8)),
    "time_out": (316.7, TY(531.9)),
    "hours":    (364.6, TY(549.2)),
    # Signatures: Emp Sig box x195 y665.3 ; date x427 y665.3
    # Sup x148.8 y690.5 ; sup date x429.6 y690.5
    "emp_sig":    (195, TY(665.3)),
    "emp_sig_date":(427, TY(665.3)),
    "sup_name":   (148, TY(690.5)),
    "sup_date":   (429, TY(690.5)),
}

def hhmm(minutes):
    m = minutes % (24 * 60)
    h = m // 60
    mm = m % 60
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{mm:02d} {ap}"

def build_entry(day, seed, facility):
    rnd = random.Random(seed)
    time_in = rnd.choice([360, 390, 420, 450, 480])   # 6:00-8:00 AM
    total_work = 480                                    # exactly 8 hours
    first = rnd.choice([240, 270, 300, 310, 330])    # 4h-5h30 before lunch
    meal_start = time_in + first
    meal_dur = rnd.choice([30, 60])
    meal_end = meal_start + meal_dur
    second = total_work - first
    time_out = meal_end + second
    # lunch at 'first' elapsed (<=330 min) is < 480 -> taken before the 8h mark
    return {
        "facility": facility,
        "date": day.strftime("%m/%d/%Y"),
        "time_in": hhmm(time_in),
        "meal_start": hhmm(meal_start),
        "meal_end": hhmm(meal_end),
        "time_out": hhmm(time_out),
        "hours": "8.00",
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--facility", default="IT Dept")
    ap.add_argument("--out", default=r"C:\Users\kevin\TARF_IT_Jul5-15")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    start = date.fromisoformat(a.start)
    end = date.fromisoformat(a.end)
    idx = 1
    day = start
    while day <= end:
        entry = build_entry(day, seed=day.toordinal(), facility=a.facility)
        ov = os.path.join(a.out, f"_ov_{idx:02d}.pdf")
        c = canvas.Canvas(ov, pagesize=letter)
        c.setFont("Helvetica-Bold", 12)
        # header facility: if facility != "SC RESOURCE", white-out the baked-in
        # "SC RESOURCE" in the template FIRST (see notes at top / generate_it_tarf.py).
        # For "IT Dept" the proven flow white-outs then inserts; this script assumes the
        # template already has the desired title OR you pre-stamp it. To stamp here:
        if a.facility != "SC RESOURCE":
            c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 95, a.facility)
        c.setFont("Helvetica", 9)
        c.drawString(*coords["employee_name"], EMPLOYEE_NAME)
        c.drawString(*coords["position"], POSITION)
        c.drawString(*coords["employee_id"], EMP_ID)
        c.drawString(*coords["missed_punch_box"], "X")
        c.drawString(*coords["date"], entry["date"])
        c.drawString(*coords["am_shift_box"], "X")
        c.drawString(*coords["time_in"], entry["time_in"])
        c.drawString(*coords["meal_start"], entry["meal_start"])
        c.drawString(*coords["meal_end"], entry["meal_end"])
        c.drawString(*coords["time_out"], entry["time_out"])
        c.drawString(*coords["hours"], entry["hours"])
        c.drawString(*coords["emp_sig"], EMP_SIG)
        c.drawString(*coords["emp_sig_date"], entry["date"])
        if SUP_NAME:
            c.drawString(*coords["sup_name"], SUP_NAME)
        # supervisor date LEFT BLANK per request
        c.showPage()
        c.save()

        out_pdf = os.path.join(a.out, f"TARF {day.month}.{day.day} {a.facility}.pdf")
        reader = PdfReader(TEMPLATE_PDF)
        template_page = reader.pages[0]
        ov_r = PdfReader(ov)
        template_page.merge_page(ov_r.pages[0])
        writer = PdfWriter()
        writer.add_page(template_page)
        with open(out_pdf, "wb") as f:
            writer.write(f)
        os.remove(ov)
        print(f"Created {out_pdf}  | {entry['time_in']} lunch {entry['meal_start']}-{entry['meal_end']} {entry['time_out']} (8.00h)")
        day += timedelta(days=1)
        idx += 1
    print("Done.")

if __name__ == "__main__":
    main()
