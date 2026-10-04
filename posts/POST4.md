# Reddit Post 4: Arch Linux & Rolling Release Clean Setup Guide

> **Target Subreddits:**
> - `r/archlinux`
> - `r/arch`
> - `r/EndeavourOS`
> - `r/linuxquestions`
>
> **Recommended Attached Graphic:**
> `posts/assets/promo-card.png` *(or `posts/assets/comparison-graphic.png`)*
>
> **Best Timing:**
> Midday or afternoon (13:00–18:00 UTC / 09:00–14:00 EST)

---

## 📌 Suggested Titles (Tailored for Arch & Power Users)

- **Option A (Arch Hygiene Hook - Recommended):**  
  `How to install and run Google Antigravity (IDE, Hub & CLI) cleanly on Arch Linux without polluting /opt`

- **Option B (Practical & Package-Centric):**  
  `Google Antigravity on Arch Linux: Clean installation guide (debtap pacman integration + user-space CLI)`

- **Option C (Community & Roadmap):**  
  `Running Google Antigravity on Arch: Native package conversion, zero-sudo CLI agent, and AUR status update`

---

## 📝 Post Body (Copy & Paste to Reddit)

*(Attach `promo-card.png` or `comparison-graphic.png` as the post image)*

If you’re running Arch Linux or an Arch-based distro (EndeavourOS, Manjaro) and want to test Google Antigravity (the AI code editor **Antigravity IDE**, the agent hub **Antigravity**, or the terminal agent **`agy`**), Google currently only provides raw `.tar.gz` downloads.

On Arch, dumping untracked tarballs into `/opt` or manually symlinking into `/usr/bin` is sloppy:
- `pacman` has zero record of the files.
- Desktop URL schemes (`antigravity://` and `antigravity-ide://`) for Google OAuth logins are broken unless desktop entry files are properly formatted.
- File manager context menus and shell completions are missing.
- When you want to remove it, you're stuck hunting down orphaned files.

Here is a guide to running the complete Antigravity suite cleanly on Arch, either fully tracked by `pacman`, via isolated user-space, or via automated tooling.

🌐 **Project Site:** https://x3m-industries.github.io/antigravity-packages/  
⭐ **GitHub:** https://github.com/x3m-industries/antigravity-packages  

---

### Option 1: Convert .DEB to Native Arch Package via `debtap` (Cleanest for `pacman`)

Because our automated build pipeline publishes verified, GPG-signed Debian packages with standard FHS directory structures and FreeDesktop entries, you can cleanly convert them into native Arch `.pkg.tar.zst` packages tracked by `pacman`:

```bash
# 1. Download latest release packages
curl -fsSLO https://github.com/x3m-industries/antigravity-packages/releases/latest/download/antigravity-ide_latest_amd64.deb
curl -fsSLO https://github.com/x3m-industries/antigravity-packages/releases/latest/download/antigravity_latest_amd64.deb

# 2. Convert with debtap
debtap -u
debtap antigravity-ide_latest_amd64.deb
debtap antigravity_latest_amd64.deb

# 3. Install cleanly with pacman
sudo pacman -U antigravity-ide-*.pkg.tar.zst antigravity-*.pkg.tar.zst
```

Now `pacman -Qi antigravity-ide` knows about every file, and `pacman -R` will remove it without leaving a trace.

---

### Option 2: Terminal-Only User-Space Setup (Zero Sudo / No Root)

If you only want to use Google’s terminal coding agent (**`agy`**) without touching system directories:

```bash
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --cli-only
```

- Installs canonically to `$HOME/.local/bin/agy`.
- Requires **zero root/sudo access**.
- Preserves Google’s official 15-minute background auto-updater in user-space.
- Completely avoids any conflicts with system packages or `pacman`.

---

### Option 3: Universal Installer (Interactive or Dry-Run)

We also maintain an interactive universal installer script with built-in distro detection, status inspection, and a dry-run mode:

```bash
# Preview what would be done without making changes
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --dry-run

# Run interactive installer (selects IDE + Hub + CLI with smart defaults)
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash
```

---

### 🔍 System Audit & Clean Removal

If you ever want to check what was installed or cleanly uninstall:

```bash
# Inspect installed versions and config status
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --status

# Reversibly wipe all installed packages and desktop entries
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --uninstall
```

---

### 📦 AUR Roadmap

We are currently testing native `antigravity-bin` and `antigravity-ide-bin` PKGBUILD recipes for submission to the Arch User Repository (AUR). If you’re an Arch packager and want to help test or review the PKGBUILDs, check out the [GitHub repo](https://github.com/x3m-industries/antigravity-packages) or drop a comment!
