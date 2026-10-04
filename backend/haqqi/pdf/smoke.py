"""`python -m haqqi.pdf.smoke [out/smoke.pdf]`: render a fixed Arabic paragraph (task 5.1).

Proves WeasyPrint, Pango and the bundled Noto Naskh Arabic font work on this machine:
open the file and check the letters join and run right to left.
"""

import resource
import sys
from pathlib import Path

from weasyprint import HTML

from haqqi.pdf.fonts import font_face_css

PARAGRAPH = (
    "إلى: وزارة الموارد البشرية والتوطين. "
    "الموضوع: شكوى عمالية بشأن الأجور غير المدفوعة ومكافأة نهاية الخدمة. "
    "أتقدم بهذه الشكوى وفقاً للمادة (51) البند (2) من المرسوم بقانون اتحادي رقم (33) لسنة 2021، "
    "وأطالب بمبلغ 6,229.59 درهم."
)


def render(out: Path) -> list[str]:
    """Write the PDF and return the names of the fonts embedded in it."""
    html = f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>
{font_face_css()}
body {{ font-family: "Noto Naskh Arabic"; font-size: 14pt; line-height: 1.8; }}
</style></head><body><p>{PARAGRAPH}</p></body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    document = HTML(string=html).render()
    document.write_pdf(out)
    return [font.name.decode().lstrip("/") for font in document.fonts.values()]


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out/smoke.pdf")
    fonts = render(out)
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"wrote {out} ({out.stat().st_size:,} bytes); peak memory {peak_mb:.0f} MB")
    print("embedded fonts:", ", ".join(fonts))
    if not any("Noto-Naskh-Arabic" in name for name in fonts):
        sys.exit("Noto Naskh Arabic is not embedded")


if __name__ == "__main__":
    main()
