"""Derives every logo asset from the single source file assets/brand/Logo.png.

Run:  python ui/make_logos.py

Source: transparent PNG, dark-blue book/arrow mark above the "EduPath-AI" wordmark.
Outputs (assets/brand/):
  logo_full.png / logo_full_dark.png   mark + wordmark, cropped tight (README, light / dark backgrounds)
  logo_mark.png / logo_mark_dark.png   mark only, cropped tight, 2x height for crisp UI use (nav, footer)
  ../favicon.png                       mark on a white rounded tile so it reads in light and dark browser tabs
The dark variants keep the brand hue but lighten it, because #154BA1 on a navy background has too little contrast.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BRAND = Path(__file__).resolve().parent.parent / "assets" / "brand"
SOURCE = BRAND / "Logo.png"
DARK_TINT = (127, 166, 255)      # light tint of the brand blue for dark backgrounds
MARK_HEIGHT = 120                 # shown at ~38-44 px in the UI, so this is ~3x for retina screens
PAD = 10


def crop(img: Image.Image, y0=None, y1=None, pad=PAD) -> Image.Image:
    """Crop to the visible pixels (optionally within a row band) and add transparent padding."""
    a = np.array(img)[:, :, 3]
    if y0 is not None:
        a = a.copy()
        a[:y0], a[y1:] = 0, 0
    ys, xs = np.where(a > 8)
    box = (xs.min() - pad, ys.min() - pad, xs.max() + 1 + pad, ys.max() + 1 + pad)
    return img.crop(box)


def tint(img: Image.Image, rgb) -> Image.Image:
    """Recolour every visible pixel, keeping the original alpha (so anti-aliased edges stay smooth)."""
    arr = np.array(img)
    arr[:, :, :3] = rgb
    return Image.fromarray(arr, "RGBA")


def bands(img: Image.Image):
    """Row ranges of the mark and the wordmark, found from the blank gap between them."""
    rows = (np.array(img)[:, :, 3] > 8).sum(axis=1)
    ys = np.where(rows > 0)[0]
    gaps = [y for y in range(ys[0], ys[-1]) if rows[y] == 0]
    split = gaps[0]
    return (ys[0], split), (gaps[-1] + 1, ys[-1] + 1)


def main():
    src = Image.open(SOURCE).convert("RGBA")
    (m0, m1), _text = bands(src)

    full = crop(src)
    mark = crop(src, m0, m1 + 1)
    scale = MARK_HEIGHT / mark.height
    mark = mark.resize((round(mark.width * scale), MARK_HEIGHT), Image.LANCZOS)

    outputs = {
        "logo_full.png": full, "logo_full_dark.png": tint(full, DARK_TINT),
        "logo_mark.png": mark, "logo_mark_dark.png": tint(mark, DARK_TINT),
    }
    for name, img in outputs.items():
        img.save(BRAND / name, optimize=True)
        print(f"{name:22s} {img.width}x{img.height}")

    # Favicon: white rounded tile + centred mark (visible on both light and dark tab strips).
    size = 256
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle((4, 4, size - 4, size - 4), radius=56, fill=(255, 255, 255, 255))
    glyph = crop(src, m0, m1 + 1, pad=0)
    glyph.thumbnail((size * 0.64, size * 0.64), Image.LANCZOS)
    tile.alpha_composite(glyph, ((size - glyph.width) // 2, (size - glyph.height) // 2))
    tile.resize((128, 128), Image.LANCZOS).save(BRAND.parent / "favicon.png", optimize=True)
    print("favicon.png            128x128")


if __name__ == "__main__":
    main()
