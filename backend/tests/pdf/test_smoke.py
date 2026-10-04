from pathlib import Path

from haqqi.pdf.smoke import render


def test_smoke_pdf_embeds_noto_naskh_arabic(tmp_path: Path) -> None:
    out = tmp_path / "smoke.pdf"
    fonts = render(out)
    assert out.read_bytes().startswith(b"%PDF-")
    assert any("Noto-Naskh-Arabic" in name for name in fonts)
