"""@font-face rules for the self-hosted Noto fonts (see fonts/README.md)."""

from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent / "fonts"

FAMILIES = {
    "Noto Naskh Arabic": "NotoNaskhArabic.ttf",
    "Noto Nastaliq Urdu": "NotoNastaliqUrdu.ttf",
    "Noto Sans Devanagari": "NotoSansDevanagari.ttf",
    "Noto Sans Malayalam": "NotoSansMalayalam.ttf",
    "Noto Sans Bengali": "NotoSansBengali.ttf",
    "Noto Sans": "NotoSans.ttf",
}

# Font stack for each language's column. Noto Sans follows for Latin text and digits.
LANGUAGE_FONTS = {
    "ar": "Noto Naskh Arabic",
    "ur": "Noto Nastaliq Urdu",
    "hi": "Noto Sans Devanagari",
    "ne": "Noto Sans Devanagari",
    "ml": "Noto Sans Malayalam",
    "bn": "Noto Sans Bengali",
    "en": "Noto Sans",
    "tl": "Noto Sans",
}


def font_face_css() -> str:
    return "\n".join(
        f'@font-face {{ font-family: "{family}"; src: url("{(FONT_DIR / file).as_uri()}"); }}'
        for family, file in FAMILIES.items()
    )


def font_stack(lang: str) -> str:
    return f'"{LANGUAGE_FONTS[lang]}", "Noto Naskh Arabic", "Noto Sans"'
