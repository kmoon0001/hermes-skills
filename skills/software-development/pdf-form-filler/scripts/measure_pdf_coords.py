"""
measure_pdf_coords.py — derive reportlab-safe field coordinates from a
NON-interactive blank PDF (no AcroFields), so you NEVER inherit hand-tuned
coords that land in the wrong box (this bit us on 2026-07-15: the
shipped tarf_range_generator.py coords were tuned for a DIFFERENT blank and
put the date in "Comments", times in "Dept Transfer", signature blank).

WHY PyMuPDF not pdfplumber: PyMuPDF get_text('words') returns
(x0, y0, x1, y1) in TOP-LEFT origin at 72dpi — exact for measuring
drawn label boxes. reportlab canvas uses BOTTOM-LEFT origin at 72dpi,
same 612x792 page. So:  reportlab_y = 792 - pymupdf_top_y.

USAGE:
  python measure_pdf_coords.py path/to/blank.pdf
Prints, per label word, the box rect + the recommended reportlab insertion
point (nudged ~10pt below the label baseline for text, -6 for checkbox X).

Then in your generator: define TY(top_y) = 792 - top_y  and use the
measured points. Re-verify with vision_analyze on a rendered sample — text
extraction LIES about white-out/overlay position, only a screenshot tells truth.
"""
import sys
import fitz  # PyMuPDF

def main():
    if len(sys.argv) < 2:
        print("usage: python measure_pdf_coords.py <blank.pdf>")
        return
    src = sys.argv[1]
    doc = fitz.open(src)
    page = doc[0]
    words = page.get_text("words")  # x0,y0,x1,y1,text,...
    print(f"# Page size: {page.rect.width} x {page.rect.height} (origin TOP-left)")
    print("# Label -> box rect (top-left y) -> reportlab insertion pt")
    labels = ["Employee", "Position", "Employee ID", "Missed", "A.M.", "P.M.",
              "Night", "Time In", "Meal", "Time Out", "Total", "Hours",
              "Date of", "Signature", "Supervisor", "SC", "RESOURCE"]
    for w in words:
        t = w[4]
        if any(k in t for k in labels):
            x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
            rl_x = x0 + 3
            rl_y = 792 - y0 - 10   # ~10pt below label baseline
            print(f"  label={t!r:18} box=({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f})  "
                  f"reportlab_pt=({rl_x:.1f}, {rl_y:.1f})")
    # checkbox X marks: place ~6pt BELOW the label baseline so X sits INSIDE the box
    print("# Checkbox X tip: use reportlab_y = (792 - label_y) - 6")
    doc.close()

if __name__ == "__main__":
    main()
