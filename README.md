# Google Antigravity & Antigravity IDE Linux Packages

<p align="center">
  <img src="assets/logo.png" width="76" height="76" alt="Google Antigravity IDE" title="Antigravity IDE" style="border-radius: 18px; margin-right: 12px; vertical-align: middle;" />
  <img src="assets/hub-logo.png" width="76" height="76" alt="Google Antigravity Hub" title="Antigravity HUB" style="border-radius: 18px; vertical-align: middle;" />
</p>

<p align="center">
  <a href="https://github.com/x3m-industries/antigravity-packages/actions/workflows/build-and-publish.yml"><img src="https://github.com/x3m-industries/antigravity-packages/actions/workflows/build-and-publish.yml/badge.svg" alt="Build Status" /></a>
  <a href="https://github.com/x3m-industries/antigravity-packages/releases"><img src="https://img.shields.io/github/downloads/x3m-industries/antigravity-packages/total?color=8b5cf6&logo=github&label=Downloads" alt="Total Downloads" /></a>
  <a href="https://x3m-industries.github.io/antigravity-packages/"><img src="https://img.shields.io/badge/Repository-Online-10b981" alt="Repository Status" /></a>
  <img src="https://img.shields.io/badge/Architectures-x86__64%20%7C%20aarch64-6366f1" alt="Architectures" />
  <img src="https://img.shields.io/badge/Signatures-GPG%20Signed-38bdf8" alt="GPG Signed" />
</p>

> **Community RPM (DNF) and DEB (APT) repositories for Google Antigravity & Antigravity IDE.**  
> Packaged & maintained by **Steven Ceuppens** at **X3M Industries**.  
> Automatically synchronized with Google's official release CDN, packaged natively for Linux with desktop application menus, high-resolution icons, and browser OAuth redirect integration.

---

## 📦 Two Official Google Packages Delivered

Google publishes official Linux binaries for both apps as standalone archives without native package repositories. This repository packages them into standard RPM and DEB packages for easy installation and ongoing updates:

| Icon | Package | Official Google App | Packaging Highlights & System Integration | Official Product Info |
| :---: | :--- | :--- | :--- | :--- |
| <img src="assets/logo.png" width="36" height="36" alt="Antigravity IDE" style="border-radius:8px;"> | **`antigravity-ide`** | **[Google Antigravity IDE](https://antigravity.google/product/antigravity-ide)**<br>AI-first desktop code editor | `antigravity-ide` command in `/usr/bin`, GNOME/KDE `.desktop` launcher, 1024px icon, `antigravity-ide://` OAuth browser handler | [antigravity.google/product/antigravity-ide](https://antigravity.google/product/antigravity-ide) |
| <img src="assets/hub-logo.png" width="36" height="36" alt="Antigravity HUB" style="border-radius:8px;"> | **`antigravity`** | **[Google Antigravity Hub](https://antigravity.google/product/antigravity-2)**<br>Agent platform & workspace (2.0) | `antigravity` command in `/usr/bin`, `.desktop` launcher, seamless `dnf`/`apt` updates | [antigravity.google/product/antigravity-2](https://antigravity.google/product/antigravity-2) |

> ℹ️ **Note on `agy`:** The standalone terminal CLI tool (`agy`) is distributed separately by Google via its own CLI installer.

> 💡 **Install together or standalone:** Run `sudo dnf install antigravity-ide antigravity` (or `apt install ...`) for both applications, or install `antigravity` standalone.

---

## 🚀 Quick Installation

### ⚡ Universal One-Line Installer (Recommended)
Automatically detects your Linux distribution (Fedora, RHEL, CentOS, Ubuntu, Debian, Rocky, Alma, openSUSE), configures repository GPG keys, and installs Antigravity:

```bash
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash
```

---

### Manual Installation by Distribution

#### Fedora / RHEL / CentOS Stream / Rocky / AlmaLinux (DNF)

```bash
# 1. Add the repository
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo

# 2. Install Antigravity IDE & Hub
sudo dnf install antigravity-ide antigravity

# 3. Update anytime
sudo dnf update antigravity-ide
```

---

#### Ubuntu / Debian / Pop!_OS / Linux Mint (APT)

```bash
# 1. Add the GPG key & APT sources (modern DEB822 format)
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources

# 2. Update and install
sudo apt update
sudo apt install antigravity-ide antigravity

# 3. Update anytime
sudo apt update && sudo apt install --only-upgrade antigravity-ide antigravity
```

---

#### Arch Linux / Manjaro / EndeavourOS

Prebuilt binaries and standalone packages are published with every release:
* **Standalone Tarballs:** Available directly on our [GitHub Releases](https://github.com/x3m-industries/antigravity-packages/releases).
* **RPM Extraction:** Extract natively using `rpmextract` or convert with `debtap`:
  ```bash
  debtap antigravity-ide_*_amd64.deb
  sudo pacman -U antigravity-ide-*.pkg.tar.zst
  ```
* **AUR:** Official `antigravity-bin` and `antigravity-ide-bin` PKGBUILDs coming soon.

---

### 🔄 Updating Antigravity
The repositories synchronize daily with Google's CDN. To update your installation:
* **Fedora / RHEL / Rocky:** `sudo dnf update antigravity-ide antigravity`
* **Ubuntu / Debian / Mint:** `sudo apt update && sudo apt install --only-upgrade antigravity-ide antigravity`

---

## 💻 Command-Line & Desktop Integration

Both packages automatically install binaries and symlinks into `/usr/bin`:

```bash
# Open any project folder
antigravity-ide ./my-project

# Open specific files
antigravity-ide main.py

# Compare files with built-in diff viewer
antigravity-ide --diff old.py new.py

# Launch Antigravity Hub
antigravity
```

### ✨ Native Desktop Features Included:
* **Browser OAuth Callback Handling:** Pre-registered `antigravity-ide://` and `antigravity://` URL scheme handlers so Google authentication redirects straight back into the running app.
* **High-Resolution Icons:** Extracted official 1024x1024 application icons placed in FreeDesktop icon themes and `/usr/share/pixmaps`.
* **System Application Menu:** GNOME, KDE, and XFCE desktop entries with quick action shortcuts (New Empty Window, etc.).

---

## 📦 Packages & Architectures

| Package | Description | Architectures |
| :--- | :--- | :--- |
| **`antigravity-ide`** | Google's VS Code–based agentic coding environment | `x86_64`, `aarch64` / `arm64` |
| **`antigravity`** | Antigravity agent runtime & background platform | `x86_64`, `aarch64` / `arm64` |

---

## 🔐 GPG Security & Package Verification

Every RPM and DEB package published through this repository is cryptographically signed to ensure authenticity and prevent tampering:

* **Packager:** `X3M Antigravity Packagers <packaging@x3m.industries>`
* **Key ID:** `7A48CA4D7E7B6601`
* **Fingerprint:** `E83A 23BC 57FE 6953 E4B5  F465 7A48 CA4D 7E7B 6601`
* **Public Key:** [RPM-GPG-KEY-antigravity](https://x3m-industries.github.io/antigravity-packages/RPM-GPG-KEY-antigravity)

---

## ⚙️ Development & Automation

### How it works
1. **Daily Upstream Check:** A GitHub Actions cron job runs daily at `05:00 UTC` to check [antigravity.google/download](https://antigravity.google/download) for new releases.
2. **Automated Packaging:** When a new version is detected, the workflow downloads the official tarballs for both `x86_64` and `aarch64`.
3. **Signing & Deployment:** Packages are signed with GPG, uploaded to GitHub Releases (handling >100 MB assets), and repository metadata (`repodata/` and `Packages.gz`) is refreshed on GitHub Pages.

### Local Development
This repository uses [mise](https://mise.jdx.dev/) for local environment management:

```bash
# Clone the repository
git clone https://github.com/x3m-industries/antigravity-packages.git
cd antigravity-packages

# Install required tools
mise install

# Check upstream release status
python3 scripts/check_upstream.py
```

### 📊 Download & Usage Analytics

Track real-time downloads across packages, architectures, and distro formats:

```bash
# Display download metrics dashboard
./scripts/stats.py

# Export raw JSON metrics
./scripts/stats.py --json
```

---

<p align="center">
  Packaged &amp; maintained by <strong>Steven Ceuppens</strong> at <a href="https://github.com/x3m-industries"><strong>X3M Industries</strong></a>
</p>
