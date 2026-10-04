#!/usr/bin/env python3
"""
Design System & Automated Image Generator for Google Antigravity Linux.
Generates Reddit promotional graphics and OpenGraph / Twitter metadata cards.

Theme tokens and layout match templates/index.html (Next.js / @vercel/og style):
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
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ASSETS_DIR = Path("assets")
POSTS_ASSETS_DIR = Path("posts/assets")
POSTS_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

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
    """Applies smooth rounded corners with antialiased mask."""
    mask = Image.new('L', (img.width * 2, img.height * 2), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), (img.width * 2, img.height * 2)], radius=radius * 2, fill=255)
    mask = mask.resize(img.size, Image.Resampling.LANCZOS)
    
    rounded = Image.new('RGBA', img.size, (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask=mask)
    return rounded

def draw_window_dots(draw, x, y):
    """Draws macOS / GNOME terminal header dots."""
    draw.ellipse([x, y, x + 12, y + 12], fill=(239, 68, 68))
    draw.ellipse([x + 20, y, x + 32, y + 12], fill=(245, 158, 11))
    draw.ellipse([x + 40, y, x + 52, y + 12], fill=(34, 197, 94))

def draw_status_dot(draw, cx, cy, radius, color):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

def draw_check_icon(draw, cx, cy, radius=11, color=(16, 185, 129)):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(color[0], color[1], color[2], 40), outline=color, width=2)
    draw.line([(cx - 5, cy), (cx - 2, cy + 3)], fill=color, width=2)
    draw.line([(cx - 2, cy + 3), (cx + 5, cy - 4)], fill=color, width=2)

def draw_cross_icon(draw, cx, cy, radius=11, color=(239, 68, 68)):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(color[0], color[1], color[2], 40), outline=color, width=2)
    draw.line([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=color, width=2)
    draw.line([(cx + 4, cy - 4), (cx - 4, cy + 4)], fill=color, width=2)


# ---------------------------------------------------------------------------
# Graphic 1: Promo Card (1200x675, Exactly 2 Logos)
# ---------------------------------------------------------------------------
def generate_promo_card():
    W, H = 1200, 675
    img = create_base_canvas(W, H)
    draw = ImageDraw.Draw(img)

    # 1. Top Bar: EXACTLY 2 LOGOS (Antigravity IDE & Antigravity Hub)
    # Both rendered at 76x76 with 18px rounded corners and subtle card border
    icon_y = 52
    ide_raw = Image.open(ASSETS_DIR / "logo.png").convert("RGBA").resize((76, 76), Image.Resampling.LANCZOS)
    hub_raw = Image.open(ASSETS_DIR / "hub-logo.png").convert("RGBA").resize((76, 76), Image.Resampling.LANCZOS)

    ide_icon = round_corners(ide_raw, 18)
    hub_icon = round_corners(hub_raw, 18)

    # Paste the 2 distinct official logos
    img.paste(ide_icon, (60, icon_y), ide_icon)
    img.paste(hub_icon, (150, icon_y), hub_icon)

    # Subtle outlines around icons for depth
    draw.rounded_rectangle([60, icon_y, 60 + 76, icon_y + 76], radius=18, outline=(255, 255, 255, 40), width=1)
    draw.rounded_rectangle([150, icon_y, 150 + 76, icon_y + 76], radius=18, outline=(255, 255, 255, 40), width=1)

    # Pill badge next to the 2 logos
    badge_x = 248
    badge_y = 70
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 360, badge_y + 36], radius=18, fill=(30, 41, 59, 230), outline=(99, 102, 241, 200), width=1)
    draw_status_dot(draw, badge_x + 18, badge_y + 18, 4, COLORS["accent"])
    b_font = font(FONT_SANS_BOLD, 13)
    draw.text((badge_x + 30, badge_y + 9), "NATIVE LINUX REPOSITORIES & SUITE", font=b_font, fill=COLORS["primary_light"])

    # Author badge
    m_font = font(FONT_SANS_REGULAR, 15)
    draw.text((badge_x + 380, badge_y + 9), "Maintained by X3M Industries", font=m_font, fill=COLORS["text_muted"])

    # 2. Main Title & Subtitle
    title_font = font(FONT_SANS_BOLD, 46)
    draw.text((60, 150), "Google Antigravity for Linux", font=title_font, fill=COLORS["text_main"])

    sub_font = font(FONT_SANS_REGULAR, 22)
    draw.text((60, 212), "Native RPM (DNF) & DEB (APT) packages for Antigravity IDE, Hub & CLI", font=sub_font, fill=COLORS["text_muted"])

    # 3. Distro Tags
    distros = [
        ("Fedora / RHEL", (37, 99, 235), (219, 234, 254)),
        ("Ubuntu / Debian", (217, 70, 0), (255, 237, 213)),
        ("Arch Linux", (2, 132, 199), (224, 242, 254)),
        ("Linux Mint", (21, 128, 61), (220, 252, 231)),
        ("openSUSE", (101, 163, 13), (236, 252, 203)),
    ]
    pill_x = 60
    pill_y = 258
    p_font = font(FONT_SANS_BOLD, 14)
    for name, border_col, text_col in distros:
        bbox = draw.textbbox((0, 0), name, font=p_font)
        pw = (bbox[2] - bbox[0]) + 30
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pw, pill_y + 32], radius=16, fill=(15, 23, 42, 230), outline=border_col, width=1)
        draw_status_dot(draw, pill_x + 13, pill_y + 16, 4, border_col)
        draw.text((pill_x + 23, pill_y + 7), name, font=p_font, fill=text_col)
        pill_x += pw + 12

    # 4. Terminal Command Box (macOS / GNOME Window style)
    term_x, term_y, term_w, term_h = 60, 312, 1080, 140
    draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h], radius=16, fill=COLORS["code_bg"], outline=(255, 255, 255, 28), width=1)

    draw_window_dots(draw, term_x + 20, term_y + 18)
    t_hdr_font = font(FONT_SANS_REGULAR, 14)
    draw.text((term_x + 88, term_y + 15), "Universal Linux 1-Command Installer (Interactive or Headless)", font=t_hdr_font, fill=COLORS["text_muted"])

    # Code Line
    c_bold = font(FONT_MONO_BOLD, 21)
    cmd_str = "curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash"
    draw.text((term_x + 24, term_y + 60), "$", font=c_bold, fill=COLORS["accent"])
    draw.text((term_x + 48, term_y + 60), cmd_str, font=c_bold, fill=COLORS["text_main"])

    c_hint = font(FONT_MONO_REGULAR, 14)
    draw.text((term_x + 48, term_y + 98), "# Selects IDE, Hub & CLI by default · Zero sudo needed for --cli-only", font=c_hint, fill=COLORS["text_muted"])

    # 5. Bento Feature Cards Row
    features = [
        ("GPG Signed", "Verified maintainer keys"),
        ("Daily Auto-Sync", "Zero-delay upstream releases"),
        ("OAuth Login Fixed", "antigravity:// protocol handler"),
        ("Context Menus", "Nautilus, Dolphin, Nemo, Caja"),
        ("agy CLI Included", "No root required, auto-updating"),
    ]
    card_w = 206
    card_h = 76
    feat_x = 60
    feat_y = 476
    f_title_f = font(FONT_SANS_BOLD, 15)
    f_desc_f = font(FONT_SANS_REGULAR, 12)

    for i, (f_title, f_desc) in enumerate(features):
        cx = feat_x + i * (card_w + 12)
        draw.rounded_rectangle([cx, feat_y, cx + card_w, feat_y + card_h], radius=12, fill=COLORS["card_bg"], outline=COLORS["card_border"], width=1)
        draw_status_dot(draw, cx + 18, feat_y + 24, 4, COLORS["accent"])
        draw.text((cx + 30, feat_y + 14), f_title, font=f_title_f, fill=COLORS["text_main"])
        draw.text((cx + 14, feat_y + 42), f_desc, font=f_desc_f, fill=COLORS["text_muted"])

    # 6. Bottom Meta Footer
    foot_font = font(FONT_MONO_REGULAR, 14)
    draw.text((60, 610), "* GitHub: github.com/x3m-industries/antigravity-packages", font=foot_font, fill=COLORS["text_muted"])
    site_str = "Docs & Repos: x3m-industries.github.io/antigravity-packages"
    s_bbox = draw.textbbox((0, 0), site_str, font=foot_font)
    draw.text((W - 60 - (s_bbox[2] - s_bbox[0]), 610), site_str, font=foot_font, fill=COLORS["accent"])

    output_path = POSTS_ASSETS_DIR / "promo-card.png"
    img.save(output_path, format="PNG", optimize=True)
    print(f"✓ Saved updated promo card to {output_path}")


# ---------------------------------------------------------------------------
# Graphic 2: Comparison Graphic (1200x675)
# ---------------------------------------------------------------------------
def generate_comparison_graphic():
    W, H = 1200, 675
    img = create_base_canvas(W, H)
    draw = ImageDraw.Draw(img)

    # Title
    t_font = font(FONT_SANS_BOLD, 36)
    sub_font = font(FONT_SANS_REGULAR, 20)
    draw.text((60, 44), "Google Antigravity on Linux: Why Packaging Matters", font=t_font, fill=COLORS["text_main"])
    draw.text((60, 94), "Why extracting raw tarballs into /opt causes headaches — and how native repositories solve it", font=sub_font, fill=COLORS["text_muted"])

    col_y = 142
    col_w = 525
    col_h = 445

    # Left Column: Raw Tarball Extractors
    col1_x = 60
    draw.rounded_rectangle([col1_x, col_y, col1_x + col_w, col_y + col_h], radius=18, fill=(24, 24, 32, 220), outline=(239, 68, 68, 120), width=1)

    c1_title_f = font(FONT_SANS_BOLD, 22)
    draw.text((col1_x + 28, col_y + 24), "Raw Tarballs Unpacked to /opt", font=c1_title_f, fill=(248, 113, 113))

    tarball_points = [
        ("No Package Manager Integration", "System database (RPM/APT) has zero knowledge of files"),
        ("Manual & Broken Upgrades", "Must manually re-download and re-extract on every release"),
        ("SUID Sandbox Failures", "Breaks Chromium sandbox on Ubuntu 24.04+ & Fedora"),
        ("Missing Browser OAuth Callbacks", "antigravity:// redirects fail to return to your editor"),
        ("No Desktop Context Menus", "No 'Open in Antigravity' in Nautilus, Dolphin or Nemo"),
        ("Risk of Orphaned Files", "Difficult, messy uninstallation that leaves junk behind")
    ]

    p_title_f = font(FONT_SANS_BOLD, 15)
    p_desc_f = font(FONT_SANS_REGULAR, 13)

    for idx, (title, desc) in enumerate(tarball_points):
        py = col_y + 74 + idx * 58
        draw_cross_icon(draw, col1_x + 38, py + 10, radius=11, color=COLORS["danger"])
        draw.text((col1_x + 60, py), title, font=p_title_f, fill=COLORS["text_main"])
        draw.text((col1_x + 60, py + 22), desc, font=p_desc_f, fill=COLORS["text_muted"])

    # Right Column: X3M Native Repositories
    col2_x = 615
    draw.rounded_rectangle([col2_x, col_y, col2_x + col_w, col_y + col_h], radius=18, fill=(15, 30, 36, 220), outline=(34, 197, 94, 140), width=1)

    draw.text((col2_x + 28, col_y + 24), "X3M Native Linux Repositories", font=c1_title_f, fill=(74, 222, 128))

    repo_points = [
        ("Native DNF, APT & Zypper Repos", "Tracked cleanly by system package manager"),
        ("Automatic Daily Upstream Sync", "Seamless updates with sudo dnf update / apt upgrade"),
        ("Hardened SUID Sandbox Permissions", "Correct 04755 root:root permissions out of the box"),
        ("Full FreeDesktop & OAuth Protocols", "Native antigravity:// & antigravity-ide:// URL schemes"),
        ("Multi-Desktop File Manager Menus", "Right-click context integration in GNOME, KDE, Mint & MATE"),
        ("100% Auditable & Clean Removal", "Single command --status and --uninstall without leftovers")
    ]

    for idx, (title, desc) in enumerate(repo_points):
        py = col_y + 74 + idx * 58
        draw_check_icon(draw, col2_x + 38, py + 10, radius=11, color=COLORS["success"])
        draw.text((col2_x + 60, py), title, font=p_title_f, fill=COLORS["text_main"])
        draw.text((col2_x + 60, py + 22), desc, font=p_desc_f, fill=COLORS["text_muted"])

    # Footer
    f_font = font(FONT_MONO_REGULAR, 14)
    draw.text((60, 614), "* 600+ package downloads · GPG Key ID: 7A48CA4D7E7B6601", font=f_font, fill=COLORS["text_muted"])
    repo_url = "github.com/x3m-industries/antigravity-packages"
    r_bbox = draw.textbbox((0, 0), repo_url, font=f_font)
    draw.text((W - 60 - (r_bbox[2] - r_bbox[0]), 614), repo_url, font=f_font, fill=COLORS["accent"])

    output_path = POSTS_ASSETS_DIR / "comparison-graphic.png"
    img.save(output_path, format="PNG", optimize=True)
    print(f"✓ Saved updated comparison graphic to {output_path}")


# ---------------------------------------------------------------------------
# Graphic 3: CLI Terminal Card (1200x675)
# ---------------------------------------------------------------------------
def generate_cli_terminal_card():
    W, H = 1200, 675
    img = create_base_canvas(W, H)
    draw = ImageDraw.Draw(img)

    # Top CLI Icon (antigravity arch with rounded corners)
    cli_raw = Image.open(ASSETS_DIR / "antigravity.png").convert("RGBA").resize((68, 68), Image.Resampling.LANCZOS)
    cli_icon = round_corners(cli_raw, 16)
    img.paste(cli_icon, (60, 48), cli_icon)
    draw.rounded_rectangle([60, 48, 60 + 68, 48 + 68], radius=16, outline=(255, 255, 255, 40), width=1)

    t_font = font(FONT_SANS_BOLD, 36)
    draw.text((144, 46), "Google Antigravity CLI ('agy') on Linux", font=t_font, fill=COLORS["text_main"])

    sub_font = font(FONT_SANS_REGULAR, 19)
    draw.text((144, 92), "Official terminal AI agent with zero-sudo user install & native shell auto-completion", font=sub_font, fill=COLORS["text_muted"])

    # Terminal Box
    term_x, term_y, term_w, term_h = 60, 136, 1080, 390
    draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h], radius=16, fill=COLORS["code_bg"], outline=(255, 255, 255, 28), width=1)

    draw_window_dots(draw, term_x + 20, term_y + 18)
    draw.text((term_x + 88, term_y + 16), "terminal - agy v2.5.5 (x86_64-linux)", font=font(FONT_SANS_REGULAR, 13), fill=COLORS["text_muted"])

    mono_reg = font(FONT_MONO_REGULAR, 16)
    mono_bold = font(FONT_MONO_BOLD, 17)

    lines = [
        ("# 1. Install CLI into ~/.local/bin/agy (No root/sudo required):", COLORS["text_dim"], False),
        ("$ curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --cli-only", COLORS["accent"], True),
        ("", (0, 0, 0), False),
        ("# 2. Launch interactive terminal coding agent:", COLORS["text_dim"], False),
        ("$ agy", COLORS["accent"], True),
        ("✓ Connected to Antigravity 2.0 Agent Engine · Auto-updates enabled (every 15 min)", COLORS["success"], False),
        ("", (0, 0, 0), False),
        ("# 3. Ergonomic shortcuts & prompt execution:", COLORS["text_dim"], False),
        ("$ agy -p 'Refactor authentication handler to support PKCE OAuth'", COLORS["accent"], True),
        ("$ agy-ide ./frontend   # Instant shortcut to launch Antigravity IDE", COLORS["text_main"], False),
        ("$ agy-hub              # Instant shortcut to launch Antigravity Hub", COLORS["text_main"], False),
    ]

    ly = term_y + 54
    for text, col, is_bold in lines:
        if text:
            fn = mono_bold if is_bold else mono_reg
            draw.text((term_x + 24, ly), text, font=fn, fill=col)
        ly += 26

    # Bottom Bento Highlights
    pills = [
        ("User-Space Only", "Installed to ~/.local/bin/agy"),
        ("Zero Sudo Required", "Safe for restricted & corporate boxes"),
        ("15-Min Auto-Updates", "Native background updater preserved"),
        ("Bash & Zsh Completions", "Tab completion for options & models"),
    ]
    pill_w = 260
    pill_h = 72
    px = 60
    py = 546
    p_t_font = font(FONT_SANS_BOLD, 14)
    p_d_font = font(FONT_SANS_REGULAR, 12)

    for i, (p_title, p_desc) in enumerate(pills):
        cx = px + i * (pill_w + 13)
        draw.rounded_rectangle([cx, py, cx + pill_w, py + pill_h], radius=12, fill=COLORS["card_bg"], outline=COLORS["card_border"], width=1)
        draw_status_dot(draw, cx + 18, py + 22, 4, COLORS["accent"])
        draw.text((cx + 28, py + 14), p_title, font=p_t_font, fill=COLORS["text_main"])
        draw.text((cx + 14, py + 38), p_desc, font=p_d_font, fill=COLORS["text_muted"])

    # Bottom minimal link
    draw.text((60, 634), "* GitHub: github.com/x3m-industries/antigravity-packages", font=font(FONT_MONO_REGULAR, 13), fill=COLORS["text_dim"])
    draw.text((W - 380, 634), "x3m-industries.github.io/antigravity-packages", font=font(FONT_MONO_REGULAR, 13), fill=COLORS["accent"])

    output_path = POSTS_ASSETS_DIR / "cli-terminal-card.png"
    img.save(output_path, format="PNG", optimize=True)
    print(f"✓ Saved updated CLI card to {output_path}")


# ---------------------------------------------------------------------------
# Graphic 4: OpenGraph / Twitter Banner (1200x630, Standard OG size)
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
    generate_promo_card()
    generate_comparison_graphic()
    generate_cli_terminal_card()
    generate_og_banner()
