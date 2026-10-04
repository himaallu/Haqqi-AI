"""Build docs/demo.gif from real screenshots of one case (TC-02, Urdu), phone width.

Run from the repo root with the backend venv (it has Pillow):
    backend/.venv/bin/python docs/screens/make_demo_gif.py
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
FRAMES = [
    "s4-picker.png",
    "s4-story-ur.png",
    "s4-confirm-tc02-ur.png",
    "s4-progress-ur.png",
    "s4-results-tc02-ur.png",
    "s5-complaint-card-ur.png",
    "s5-complaint-pdf-ur.png",
]
WIDTH, HEIGHT = 360, 672  # one phone screen (the top of each page)


def frame(name: str) -> Image.Image:
    img = Image.open(HERE / name).convert("RGB")
    scale = WIDTH / img.width
    img = img.resize((WIDTH, round(img.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    canvas.paste(img.crop((0, 0, WIDTH, min(HEIGHT, img.height))), (0, 0))
    return canvas.quantize(colors=128, method=Image.Quantize.MEDIANCUT)


frames = [frame(name) for name in FRAMES]
out = HERE.parent / "demo.gif"
frames[0].save(out, save_all=True, append_images=frames[1:], duration=2500, loop=0, optimize=True)
print(f"{out} ({out.stat().st_size // 1024} KB, {len(frames)} frames)")
