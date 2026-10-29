"""Generate ARIA app icon — holographic 'A' with neural ring."""

from PIL import Image, ImageDraw, ImageFilter
import math
import os

SIZES = [16, 32, 48, 64, 128, 256, 512]
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def make_icon(size: int):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    cx, cy = size / 2, size / 2
    r = size * 0.46

    # Background glow (multi-layer for halo effect)
    for i, alpha in [(int(size * 0.05), 60), (int(size * 0.03), 100)]:
        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((cx - r - i, cy - r - i, cx + r + i, cy + r + i),
                   fill=(0, 229, 255, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=size * 0.04))
        img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img, "RGBA")

    # Main disc — teal-to-purple gradient via concentric rings
    steps = 60
    for i in range(steps, 0, -1):
        t = i / steps
        # Lerp teal → cyan → purple
        if t > 0.6:
            r_c = int(0 + (92 - 0) * (1 - t) / 0.4)
            g_c = int(191 + (229 - 191) * (1 - t) / 0.4)
            b_c = int(168 + (220 - 168) * (1 - t) / 0.4)
        else:
            r_c = int(92 + (179 - 92) * (1 - t) / 0.6)
            g_c = int(229 + (136 - 229) * (1 - t) / 0.6)
            b_c = int(220 + (255 - 220) * (1 - t) / 0.6)
        rr = r * t
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr),
                     fill=(r_c, g_c, b_c, 255))

    # Highlight (top-left specular)
    hl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hld = ImageDraw.Draw(hl)
    hr = r * 0.5
    hld.ellipse((cx - r * 0.5, cy - r * 0.55, cx + r * 0.1, cy - r * 0.1),
                fill=(255, 255, 255, 100))
    hl = hl.filter(ImageFilter.GaussianBlur(radius=size * 0.04))
    img = Image.alpha_composite(img, hl)

    draw = ImageDraw.Draw(img, "RGBA")

    # Neural ring (orbit dots around 'A')
    if size >= 48:
        n_dots = 8
        ring_r = r * 0.85
        for i in range(n_dots):
            ang = (i / n_dots) * math.pi * 2 - math.pi / 2
            dx = cx + math.cos(ang) * ring_r
            dy = cy + math.sin(ang) * ring_r
            dot_r = max(2, size * 0.02)
            # Halo
            draw.ellipse((dx - dot_r * 2, dy - dot_r * 2, dx + dot_r * 2, dy + dot_r * 2),
                         fill=(255, 255, 255, 80))
            draw.ellipse((dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r),
                         fill=(255, 255, 255, 240))

    # Letter A (stylized — thick stroke with neural cut)
    # Construct as triangle outline
    a_height = r * 1.2
    a_width = r * 0.95
    top = (cx, cy - a_height * 0.45)
    bl  = (cx - a_width / 2, cy + a_height * 0.40)
    br  = (cx + a_width / 2, cy + a_height * 0.40)
    stroke_w = max(2, size * 0.06)

    # Outer dark navy stroke for contrast
    draw.line([top, bl], fill=(10, 20, 40, 220), width=int(stroke_w * 1.4))
    draw.line([top, br], fill=(10, 20, 40, 220), width=int(stroke_w * 1.4))
    # Inner white stroke
    draw.line([top, bl], fill=(255, 255, 255, 255), width=int(stroke_w))
    draw.line([top, br], fill=(255, 255, 255, 255), width=int(stroke_w))
    # Crossbar
    cb_y = cy + a_height * 0.10
    cb_l = (cx - a_width * 0.28, cb_y)
    cb_r = (cx + a_width * 0.28, cb_y)
    draw.line([cb_l, cb_r], fill=(10, 20, 40, 220), width=int(stroke_w * 1.4))
    draw.line([cb_l, cb_r], fill=(255, 255, 255, 255), width=int(stroke_w))

    # Bottom-right notch (futuristic accent) — only on larger sizes
    if size >= 64:
        notch_r = max(3, size * 0.04)
        nx = cx + r * 0.55
        ny = cy + r * 0.55
        draw.ellipse((nx - notch_r * 1.6, ny - notch_r * 1.6, nx + notch_r * 1.6, ny + notch_r * 1.6),
                     fill=(255, 255, 255, 80))
        draw.ellipse((nx - notch_r, ny - notch_r, nx + notch_r, ny + notch_r),
                     fill=(255, 215, 0, 255))

    return img


def main():
    pngs = []
    for size in SIZES:
        img = make_icon(size)
        path = os.path.join(OUT_DIR, f"icon_{size}.png")
        img.save(path)
        pngs.append((size, path, img))
        print(f"  saved icon_{size}.png")

    # Write multi-resolution .ico
    ico_path = os.path.join(OUT_DIR, "icons", "aria_icon.ico")
    os.makedirs(os.path.dirname(ico_path), exist_ok=True)
    # Pillow saves .ico from a base image with sizes parameter
    base = make_icon(256)
    base.save(ico_path, format="ICO",
              sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"  saved aria_icon.ico (multi-res)")

    # Main PNG
    png_path = os.path.join(OUT_DIR, "icons", "aria_icon.png")
    base.save(png_path)
    print(f"  saved aria_icon.png 256x256")


if __name__ == "__main__":
    main()
