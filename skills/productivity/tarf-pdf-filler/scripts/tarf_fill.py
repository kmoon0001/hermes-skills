#!/usr/bin/env python
"""
tarf_fill.py  --  Fill the SC-Resource "Time Adjustment Request Form" (TARF).

Two modes:
  template   Build a clean base template (blank facility header, employee
             name/ID/role baked in, all fields empty). Reusable for any run.
  fill       Populate the template from a JSON list of entries -> one PDF each.

Coordinates were measured from blank-tarf.pdf and visually verified
(reportlab bottom-left origin, LETTER 612x792).

Defaults target Kevin Moon's template on this machine, but every value is
overridable via flags so the skill works for other employees too.
"""
import argparse
import json
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# ---- verified field coordinates (x, y) in reportlab space -------------------
COORDS = {
    "employee_name": (172, 630),
    "position":      (130, 607),
    "employee_id":   (432, 607),
    "missed_punch":  (93, 557),
    "new_hire":      (93, 539),
    "forgot":        (93, 520),
    "lost_badge":    (93, 501),
    "meal_not":      (93, 482),
    "date":          (185, 315),
    "am_shift":      (93, 287),
    "pm_shift":      (93, 269),
    "night_shift":   (93, 252),
    "time_in":       (315, 287),
    "meal_start":    (332, 270),
    "meal_end":      (410, 270),
    "time_out":      (320, 253),
    "hours":         (370, 235),
    "emp_sig":       (200, 120),
    "emp_sig_date":  (432, 120),
    "sup_name":      (200, 95),
    "sup_date":      (432, 95),
}
HEADER_RECT = (232, 702, 126, 30)   # white-out band over the facility title row

DEFAULT_EMP = {"name": "Kevin Moon", "position": "SLP", "id": "123713644"}
DEFAULT_TEMPLATE = r"C:\Users\kevin\TARF_template.pdf"
REASON_KEYS = {
    "Missed Punch": "missed_punch",
    "New Hire": "new_hire",
    "Forgot to punch": "forgot",
    "Lost Badge": "lost_badge",
    "Meal Not Taken": "meal_not",
}
SHIFT_KEYS = {"AM": "am_shift", "PM": "pm_shift", "Night": "night_shift"}


def to_min(s):
    """'8:00 AM' -> minutes since midnight."""
    t, ap = s.strip().split()
    h, m = t.split(":")
    h = int(h) % 12
    if ap.upper() == "PM":
        h += 12
    return h * 60 + int(m)


def hhmm(minutes):
    m = minutes % (24 * 60)
    h, mm = m // 60, m % 60
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{mm:02d} {ap}"


def _overlay(path, draw_fn):
    c = canvas.Canvas(path, pagesize=letter)
    draw_fn(c)
    c.showPage()
    c.save()


def make_template(out_path, emp=DEFAULT_EMP, facility=None):
    """White-out the SC RESOURCE / IT Dept band, bake name/ID/role, save."""
    ov = out_path + "._ov.pdf"

    def draw(c):
        # erase any baked facility title
        c.setFillColorRGB(1, 1, 1)
        c.rect(*HEADER_RECT, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        # optionally stamp a facility name in the (now blank) title row
        if facility:
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(295, 715, facility)
        # bake employee identity
        c.setFont("Helvetica", 9)
        c.drawString(*COORDS["employee_name"], emp["name"])
        c.drawString(*COORDS["position"], emp["position"])
        c.drawString(*COORDS["employee_id"], emp["id"])

    _overlay(ov, draw)
    reader = PdfReader(r"C:\Users\kevin\blank-tarf.pdf")
    pg = reader.pages[0]
    pg.merge_page(PdfReader(ov).pages[0])
    w = PdfWriter()
    w.add_page(pg)
    with open(out_path, "wb") as fh:
        w.write(fh)
    os.remove(ov)
    print(f"Template written -> {out_path}")


def fill_entry(template_path, e, out_path, emp=DEFAULT_EMP, sig=None):
    """Fill one entry onto the template and write out_path."""
    ov = out_path + "._ov.pdf"

    reasons = e.get("reasons", [])
    shift = e.get("shift", "AM")
    date = e["date"]
    emp_sign = e.get("employee_sign", sig or f"/s/ {emp['name']}")
    emp_sign_date = e.get("employee_sign_date", date)
    facility = e.get("facility")

    # auto-compute hours if omitted
    if "hours" not in e and all(k in e for k in ("time_in", "meal_start", "meal_end", "time_out")):
        worked = (to_min(e["meal_start"]) - to_min(e["time_in"])) + \
                 (to_min(e["time_out"]) - to_min(e["meal_end"]))
        hours = f"{worked/60:.2f}"
    else:
        hours = e.get("hours", "8.00")

    def draw(c):
        c.setFillColorRGB(1, 1, 1)
        c.rect(*HEADER_RECT, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        if facility:
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(295, 715, facility)

        c.setFont("Helvetica", 9)
        c.drawString(*COORDS["date"], date)
        # reason X marks
        for r in reasons:
            if r in REASON_KEYS:
                c.drawString(*COORDS[REASON_KEYS[r]], "X")
        # shift X
        if shift in SHIFT_KEYS:
            c.drawString(*COORDS[SHIFT_KEYS[shift]], "X")
        # times
        for k in ("time_in", "meal_start", "meal_end", "time_out"):
            if k in e:
                c.drawString(*COORDS[k], e[k])
        c.drawString(*COORDS["hours"], hours)
        # signature
        c.drawString(*COORDS["emp_sig"], emp_sign)
        c.drawString(*COORDS["emp_sig_date"], emp_sign_date)
        # supervisor (default blank)
        if e.get("supervisor"):
            c.drawString(*COORDS["sup_name"], e["supervisor"])
        if e.get("supervisor_date"):
            c.drawString(*COORDS["sup_date"], e["supervisor_date"])

    _overlay(ov, draw)
    reader = PdfReader(template_path)
    pg = reader.pages[0]
    pg.merge_page(PdfReader(ov).pages[0])
    w = PdfWriter()
    w.add_page(pg)
    with open(out_path, "wb") as fh:
        w.write(fh)
    os.remove(ov)
    return hours


def main():
    ap = argparse.ArgumentParser(description="Fill the TARF PDF.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("template", help="create the clean base template")
    t.add_argument("--out", default=DEFAULT_TEMPLATE)
    t.add_argument("--name", default=DEFAULT_EMP["name"])
    t.add_argument("--position", default=DEFAULT_EMP["position"])
    t.add_argument("--id", dest="empid", default=DEFAULT_EMP["id"])
    t.add_argument("--facility", default=None,
                   help="optional facility name stamped at top")

    f = sub.add_parser("fill", help="fill entries from a JSON file")
    f.add_argument("--template", default=DEFAULT_TEMPLATE)
    f.add_argument("--json", required=True, help="path to entries JSON (list)")
    f.add_argument("--outdir", default=".")
    f.add_argument("--name", default=DEFAULT_EMP["name"])
    f.add_argument("--position", default=DEFAULT_EMP["position"])
    f.add_argument("--id", dest="empid", default=DEFAULT_EMP["id"])
    f.add_argument("--sig", default=None, help="employee signature string")

    args = ap.parse_args()
    emp = {"name": args.name, "position": args.position, "id": args.empid}

    if args.cmd == "template":
        make_template(args.out, emp, args.facility)
    else:
        entries = json.load(open(args.json))
        os.makedirs(args.outdir, exist_ok=True)
        for e in entries:
            safe = e["date"].replace("/", "-")
            out = os.path.join(args.outdir, f"TARF {safe}.pdf")
            h = fill_entry(args.template, e, out, emp, args.sig)
            print(f"  {out}  shift={e.get('shift','AM')}  hours={h}")


if __name__ == "__main__":
    main()
