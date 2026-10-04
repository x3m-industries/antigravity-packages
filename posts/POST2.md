# Reddit Post 2: Linux Distro Engineering & Hardening Deep-Dive

> **Target Subreddits:**
> - `r/Fedora`
> - `r/linux`
> - `r/Ubuntu`
> - `r/debian`
>
> **Recommended Attached Graphic:**
> `posts/assets/comparison-graphic.png`
>
> **Best Timing:**
> Midday or early afternoon (14:00–18:00 UTC / 10:00–14:00 EST)

---

## 📌 Suggested Titles (Tailored by Subreddit)

- **For `r/Fedora` (Recommended):**  
  `For Fedora users using Google Antigravity: I built automated native RPM repos (DNF) with GPG signing, daily sync, and SUID sandbox fixes`

- **For `r/linux` / `r/Ubuntu` / `r/debian`:**  
  `Why raw tarballs fail on modern Linux: Building automated RPM & DEB packaging infrastructure for Google Antigravity`

- **Alternative Technical Title:**  
  `Automating Google Antigravity on Linux: Native DNF/APT repos, SUID chrome-sandbox hardening, and containerized CI smoke tests`

---

## 📝 Post Body (Copy & Paste to Reddit)

*(Attach `comparison-graphic.png` as the post image)*

Google recently launched **Antigravity IDE** (AI code editor based on Code OSS) and **Antigravity Hub** (agent platform), but they currently only publish raw `.tar.gz` archives for Linux.

If you unpack Google's tarballs into `/opt` or `~/.local` manually, you quickly run into classic Linux desktop headaches:
1. **SUID Sandbox Failures:** On modern distros (Fedora with SELinux, and Ubuntu 24.04+ with restricted unprivileged user namespaces), Electron applications need `chrome-sandbox` to have strict `04755 root:root` permissions. Raw extractions break this, forcing developers to resort to dangerous `--no-sandbox` flags.
2. **Missing OAuth URL Protocols:** Google authentication redirects through browser callbacks (`antigravity://` and `antigravity-ide://`). Without registered FreeDesktop protocol handlers, web login flow drops into void.
3. **No Package Manager Tracking:** System tools have no record of installed files. Upgrades require manual re-downloads, and clean uninstallation leaves orphaned files across your filesystem.

To solve this properly for the community, I built an open-source packaging and distribution pipeline that publishes **native, verified RPM and DEB repositories** with automated daily upstream synchronization.

🌐 **Website & Documentation:** https://x3m-industries.github.io/antigravity-packages/  
⭐ **GitHub & Packaging Source:** https://github.com/x3m-industries/antigravity-packages  

---

### 🛠️ Packaging Architecture Highlights

- **Native Repositories:**
  - **Fedora / RHEL / Rocky / openSUSE (RPM):** Clean `.spec` builds with `AutoReqProv: no` to avoid pulling redundant bundled Electron shared libraries. Repository metadata is generated with `createrepo_c -u` to direct RPM downloads straight from high-speed GitHub Releases CDN.
  - **Ubuntu / Debian / Pop!_OS / Mint (DEB):** Full support for modern **DEB822** format (`/etc/apt/sources.list.d/antigravity.sources`) using signed `InRelease` and detached `Release.gpg` keys.
- **SUID Permissions Sanitization:** Automatically normalizes execution trees and enforces `4755 root:root` permissions on Chromium sandboxes during RPM `%install` and DEB `postinst`.
- **GPG Signing:** Every RPM binary and APT repository release file is cryptographically signed (`Key ID: 7A48CA4D7E7B6601`, maintainer key `X3M Antigravity Packagers <packaging@x3m.industries>`).
- **Container Smoke Tests:** Every build runs automated end-to-end installation tests in isolated Fedora and Ubuntu 24.04 containers in CI before deploying to GitHub Pages.

---

### 💻 Quick Distro Setup

#### Fedora / RHEL / CentOS Stream (DNF)
```bash
# Add repo configuration
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo

# Install Antigravity IDE and Hub
sudo dnf install antigravity-ide antigravity

# Update anytime via normal system routine
sudo dnf update antigravity-ide antigravity
```

#### Ubuntu / Debian / Pop!_OS (APT)
```bash
# Add GPG key and modern DEB822 source
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources

# Install
sudo apt update
sudo apt install antigravity-ide antigravity
```

#### Or via Universal 1-Command Installer
```bash
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash
```

---

### 🔍 System Audit & Clean Removal

We built full auditability into the tooling so you never have to wonder what modified your system:
```bash
# Inspect installed versions, repo configurations, and GPG key status
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --status

# Cleanly remove packages, repositories, and context extensions
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --uninstall
```

All build scripts, specs, and CI workflows are fully open-source and auditable on GitHub. Feedback from Fedora, Debian, and Ubuntu maintainers is very welcome!
