# Google Antigravity & Antigravity IDE Linux Packages

<p align="center">
  <a href="https://github.com/x3m-industries/antigravity-packages/actions/workflows/build-and-publish.yml"><img src="https://github.com/x3m-industries/antigravity-packages/actions/workflows/build-and-publish.yml/badge.svg" alt="Build Status" /></a>
  <a href="https://github.com/x3m-industries/antigravity-packages/releases"><img src="https://img.shields.io/github/downloads/x3m-industries/antigravity-packages/total?color=8b5cf6&logo=github&label=Downloads" alt="Total Downloads" /></a>
  <a href="https://x3m-industries.github.io/antigravity-packages/"><img src="https://img.shields.io/badge/Repository-Online-10b981" alt="Repository Status" /></a>
  <img src="https://img.shields.io/badge/Architectures-x86__64%20%7C%20aarch64-6366f1" alt="Architectures" />
  <img src="https://img.shields.io/badge/Signatures-GPG%20Signed-38bdf8" alt="GPG Signed" />
</p>

> **Community RPM (DNF) and DEB (APT) repositories for Google Antigravity & Antigravity IDE.**  
> Automatically synchronized with Google's official release CDN, packaged natively for Linux with full CLI, high-resolution desktop icons, and browser OAuth redirect integration.

---

## 🚀 Quick Installation

### Fedora / RHEL / CentOS Stream / Rocky / AlmaLinux (DNF)

```bash
# 1. Add the repository
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo

# 2. Install Antigravity IDE & Hub
sudo dnf install antigravity-ide antigravity

# 3. Update anytime
sudo dnf update antigravity-ide
```

---

### Ubuntu / Debian / Pop!_OS / Linux Mint (APT)

```bash
# 1. Add the GPG key & APT sources (modern DEB822 format)
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources

# 2. Update and install
sudo apt update
sudo apt install antigravity-ide antigravity

# 3. Update anytime
sudo apt update && sudo apt upgrade antigravity-ide
```

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
  Maintained by <a href="https://github.com/x3m-industries"><strong>X3M Industries</strong></a>
</p>
