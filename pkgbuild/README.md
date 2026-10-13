# Arch Linux Packaging (`PKGBUILD`)

This directory contains standalone Arch Linux package definitions (`PKGBUILD`) for Google Antigravity.

## Applications

1. **`antigravity-ide-bin`**: Google Antigravity IDE (Official AI Code Editor)
2. **`antigravity-bin`**: Google Antigravity Agent Hub (Antigravity 2.0 platform)

## Quick Build & Installation

### Option 1: Direct Build with `makepkg`

Clone this repository and run `makepkg -si` inside the desired directory:

```bash
# Build and install Antigravity IDE
cd pkgbuild/antigravity-ide-bin
makepkg -si

# Build and install Antigravity Hub
cd ../antigravity-bin
makepkg -si
```

### Option 2: Universal CLI Installer (No Root Required)

To install Google's official Antigravity CLI (`agy`) directly on Arch Linux:

```bash
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --cli-only
```

### Option 3: Convert via `debtap`

If you prefer installing without cloning the repository:

```bash
# 1. Install and update debtap (if not already installed)
sudo pacman -S --needed debtap
sudo debtap -u

# 2. Download and convert latest release deb
curl -fsSLO https://github.com/x3m-industries/antigravity-packages/releases/latest/download/antigravity-ide_2.5.5-4923483625488384.3_amd64.deb
debtap antigravity-ide_*.deb

# 3. Install the resulting package with pacman
sudo pacman -U antigravity-ide-*.pkg.tar.zst
```
