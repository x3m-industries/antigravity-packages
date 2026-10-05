#!/usr/bin/env python3
"""
Design System & Automated OpenGraph Banner Generator for Google Antigravity Linux.
Generates OpenGraph and Twitter metadata cards for the website landing page.

Theme tokens and layout match templates/index.html:
  --bg-color: #0b1120
  --card-bg: rgba(22, 33, 56, 0.72)
  --card-border: rgba(255, 255, 255, 0.12)
  --primary: #4f46e5
  --accent: #38bdf8
  --text-main: #f8fafc
  --text-muted: #94a3b8
  --code-bg: #020617
  --success: #10b981
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ASSETS_DIR = Path("assets")

# ---------------------------------------------------------------------------
# Design Tokens (Palette from templates/index.html)
# ---------------------------------------------------------------------------
COLORS = {
    "bg": (11, 17, 32, 255),           # #0b1120
    "bg_secondary": (15, 23, 42, 255), # #0f172a
    "card_bg": (22, 33, 56, 220),      # rgba(22, 33, 56, 0.86)
    "card_border": (255, 255, 255, 32),# rgba(255, 255, 255, 0.12)
    "code_bg": (2, 6, 23, 245),        # #020617
    "primary": (79, 70, 229),          # #4f46e5 (Indigo)
    "primary_glow": (99, 102, 241, 55),# #6366f1
    "primary_light": (199, 210, 254),  # #c7d2fe
    "accent": (56, 189, 248),          # #38bdf8 (Sky Blue)
    "accent_glow": (56, 189, 248, 45),
    "purple_glow": (168, 85, 247, 35), # #a855f7
    "text_main": (248, 250, 252),      # #f8fafc
    "text_muted": (148, 163, 184),     # #94a3b8
    "text_dim": (100, 116, 139),       # #64748b
    "success": (16, 185, 129),         # #10b981
    "danger": (239, 68, 68),           # #ef4444
    "warning": (245, 158, 11),         # #f59e0b
}

# Typography
FONT_SANS_BOLD = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"
FONT_SANS_REGULAR = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"
FONT_MONO_REGULAR = "/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Bold.ttf"

def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ---------------------------------------------------------------------------
# Reusable Component Primitives
# ---------------------------------------------------------------------------
def create_base_canvas(width, height):
    """Creates dark canvas with ambient gradients matching landing page CSS."""
    base = Image.new("RGBA", (width, height), (11, 17, 32, 255))
    draw = ImageDraw.Draw(base)

    # Subtle vertical gradient
    for y in range(height):
        r = int(11 + (15 - 11) * (y / height))
        g = int(17 + (23 - 17) * (y / height))
        b = int(32 + (42 - 32) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Ambient radial glows
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    def draw_glow(cx, cy, radius, col):
        for r in range(radius, 0, -12):
            factor = (1.0 - (r / radius) ** 0.7)
            a = int(factor * col[3])
            if a > 0:
                glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(col[0], col[1], col[2], a))

    draw_glow(width // 2, 0, 480, COLORS["primary_glow"])          # Top-center indigo
    draw_glow(int(width * 0.12), int(height * 0.3), 420, COLORS["accent_glow"])  # Left sky blue
    draw_glow(int(width * 0.88), int(height * 0.35), 450, COLORS["purple_glow"]) # Right purple
    draw_glow(width // 2, height, 400, (30, 58, 138, 40))         # Bottom subtle blue

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(16))
    canvas = Image.alpha_composite(base, glow_layer)

    # Outer border
    cdraw = ImageDraw.Draw(canvas)
    cdraw.rounded_rectangle([18, 18, width - 18, height - 18], radius=24, outline=(255, 255, 255, 28), width=2)
    return canvas

def round_corners(img, radius):
    """Applies smooth rounded corners with antialiased mask without edge darkening."""
    scale = 4
    mask = Image.new('L', (img.width * scale, img.height * scale), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), (img.width * scale, img.height * scale)], radius=radius * scale, fill=255)
    mask = mask.resize(img.size, Image.Resampling.LANCZOS)

    out = img.copy().convert('RGBA')
    r, g, b, a = out.split()
    new_a = ImageChops.multiply(a, mask)
    out.putalpha(new_a)
    return out

def draw_window_dots(draw, x, y):
    """Draws macOS / GNOME terminal header dots."""
    draw.ellipse([x, y, x + 12, y + 12], fill=(239, 68, 68))
    draw.ellipse([x + 20, y, x + 32, y + 12], fill=(245, 158, 11))
    draw.ellipse([x + 40, y, x + 52, y + 12], fill=(34, 197, 94))

def draw_status_dot(draw, cx, cy, radius, color):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

# ---------------------------------------------------------------------------
# OpenGraph / Twitter Banner (1200x630, Standard OG size)
# ---------------------------------------------------------------------------
def generate_og_banner():
    W, H = 1200, 630
    img = create_base_canvas(W, H)
    draw = ImageDraw.Draw(img)

    # 2 Logos (IDE + Hub)
    icon_y = 48
    ide_raw = Image.open(ASSETS_DIR / "logo.png").convert("RGBA").resize((76, 76), Image.Resampling.LANCZOS)
    hub_raw = Image.open(ASSETS_DIR / "hub-logo.png").convert("RGBA").resize((76, 76), Image.Resampling.LANCZOS)

    ide_icon = round_corners(ide_raw, 18)
    hub_icon = round_corners(hub_raw, 18)

    img.paste(ide_icon, (60, icon_y), ide_icon)
    img.paste(hub_icon, (150, icon_y), hub_icon)

    draw.rounded_rectangle([60, icon_y, 60 + 76, icon_y + 76], radius=18, outline=(255, 255, 255, 40), width=1)
    draw.rounded_rectangle([150, icon_y, 150 + 76, icon_y + 76], radius=18, outline=(255, 255, 255, 40), width=1)

    badge_x = 248
    badge_y = 66
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 360, badge_y + 36], radius=18, fill=(30, 41, 59, 230), outline=(99, 102, 241, 200), width=1)
    draw_status_dot(draw, badge_x + 18, badge_y + 18, 4, COLORS["accent"])
    b_font = font(FONT_SANS_BOLD, 13)
    draw.text((badge_x + 30, badge_y + 9), "NATIVE LINUX REPOSITORIES & SUITE", font=b_font, fill=COLORS["primary_light"])

    m_font = font(FONT_SANS_REGULAR, 15)
    draw.text((badge_x + 380, badge_y + 9), "Maintained by X3M Industries", font=m_font, fill=COLORS["text_muted"])

    # Title & Subtitle
    title_font = font(FONT_SANS_BOLD, 46)
    draw.text((60, 144), "Google Antigravity for Linux", font=title_font, fill=COLORS["text_main"])

    sub_font = font(FONT_SANS_REGULAR, 22)
    draw.text((60, 204), "Native RPM (DNF) & DEB (APT) repositories with daily upstream sync", font=sub_font, fill=COLORS["text_muted"])

    # Distros
    distros = [
        ("Fedora / RHEL", (37, 99, 235), (219, 234, 254)),
        ("Ubuntu / Debian", (217, 70, 0), (255, 237, 213)),
        ("Arch Linux", (2, 132, 199), (224, 242, 254)),
        ("Linux Mint", (21, 128, 61), (220, 252, 231)),
        ("openSUSE", (101, 163, 13), (236, 252, 203)),
    ]
    pill_x = 60
    pill_y = 250
    p_font = font(FONT_SANS_BOLD, 14)
    for name, border_col, text_col in distros:
        bbox = draw.textbbox((0, 0), name, font=p_font)
        pw = (bbox[2] - bbox[0]) + 30
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pw, pill_y + 32], radius=16, fill=(15, 23, 42, 230), outline=border_col, width=1)
        draw_status_dot(draw, pill_x + 13, pill_y + 16, 4, border_col)
        draw.text((pill_x + 23, pill_y + 7), name, font=p_font, fill=text_col)
        pill_x += pw + 12

    # Terminal box
    term_x, term_y, term_w, term_h = 60, 302, 1080, 134
    draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h], radius=16, fill=COLORS["code_bg"], outline=(255, 255, 255, 28), width=1)

    draw_window_dots(draw, term_x + 20, term_y + 18)
    draw.text((term_x + 88, term_y + 15), "Universal Linux 1-Command Installer (Fedora, Ubuntu, Debian, Arch, openSUSE)", font=font(FONT_SANS_REGULAR, 14), fill=COLORS["text_muted"])

    c_bold = font(FONT_MONO_BOLD, 21)
    cmd_str = "curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash"
    draw.text((term_x + 24, term_y + 60), "$", font=c_bold, fill=COLORS["accent"])
    draw.text((term_x + 48, term_y + 60), cmd_str, font=c_bold, fill=COLORS["text_main"])

    c_hint = font(FONT_MONO_REGULAR, 14)
    draw.text((term_x + 48, term_y + 96), "# Selects IDE, Hub & CLI by default · Zero sudo needed for --cli-only", font=c_hint, fill=COLORS["text_muted"])

    # Feature Row
    features = [
        ("GPG Signed", "Verified keys"),
        ("Daily Auto-Sync", "Zero delay"),
        ("OAuth Fixed", "antigravity://"),
        ("Context Menus", "Nautilus & Dolphin"),
        ("agy Included", "No sudo needed"),
    ]
    card_w = 206
    card_h = 70
    feat_x = 60
    feat_y = 458
    f_title_f = font(FONT_SANS_BOLD, 15)
    f_desc_f = font(FONT_SANS_REGULAR, 12)

    for i, (f_title, f_desc) in enumerate(features):
        cx = feat_x + i * (card_w + 12)
        draw.rounded_rectangle([cx, feat_y, cx + card_w, feat_y + card_h], radius=12, fill=COLORS["card_bg"], outline=COLORS["card_border"], width=1)
        draw_status_dot(draw, cx + 18, feat_y + 22, 4, COLORS["accent"])
        draw.text((cx + 28, feat_y + 12), f_title, font=f_title_f, fill=COLORS["text_main"])
        draw.text((cx + 14, feat_y + 38), f_desc, font=f_desc_f, fill=COLORS["text_muted"])

    # Footer
    foot_font = font(FONT_MONO_REGULAR, 14)
    draw.text((60, 568), "* GitHub: github.com/x3m-industries/antigravity-packages", font=foot_font, fill=COLORS["text_muted"])
    site_str = "x3m-industries.github.io/antigravity-packages"
    s_bbox = draw.textbbox((0, 0), site_str, font=foot_font)
    draw.text((W - 60 - (s_bbox[2] - s_bbox[0]), 568), site_str, font=foot_font, fill=COLORS["accent"])

    # Also update site OG assets
    og_png = ASSETS_DIR / "og-banner.png"
    og_webp = ASSETS_DIR / "og-banner.webp"
    img.save(og_png, format="PNG", optimize=True)
    img.save(og_webp, format="WEBP", quality=90)
    print(f"✓ Saved updated OpenGraph banner to {og_png} and {og_webp}")


if __name__ == "__main__":
    generate_og_banner()
