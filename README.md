# Google Antigravity & Antigravity IDE Linux Packages

Automated community RPM (DNF) and DEB (APT) packaging for **Google Antigravity** and **Antigravity IDE**, maintained by **[X3M Industries](https://github.com/x3m-industries)**.

This repository tracks upstream releases on [antigravity.google/download](https://antigravity.google/download), packages them into standard native `.rpm` and `.deb` packages with proper desktop integration, signs them with GPG, and serves them via public DNF and APT repositories.

---

## What is included?

* **`antigravity-ide`**: The official VS Code–based agentic coding IDE. Includes command-line access (`antigravity-ide ./project`), FreeDesktop menu shortcuts, hi-res application icons, and browser login callback handling (`antigravity-ide://`).
* **`antigravity`**: Google Antigravity agent runtime and hub background platform.

---

## 📦 Installation

### Fedora / RHEL / CentOS / Rocky / AlmaLinux (DNF)

1. **Add the repository:**
   ```bash
   sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo
   ```

2. **Install the applications:**
   ```bash
   # Install both or either
   sudo dnf install antigravity-ide antigravity
   ```

3. **Update anytime:**
   ```bash
   sudo dnf update antigravity-ide
   ```

---

### Ubuntu / Debian / Pop!_OS / Linux Mint (APT)

1. **Add the GPG key and APT repository:**
   ```bash
   sudo mkdir -p /etc/apt/keyrings
   sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
   sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources
   ```

2. **Install the applications:**
   ```bash
   sudo apt update
   sudo apt install antigravity-ide antigravity
   ```

---

## 🚀 Command-Line Usage

Both applications install symlinks into `/usr/bin`:

```bash
# Open a workspace directory
antigravity-ide ./myproject

# Open specific files
antigravity-ide main.py

# Compare files
antigravity-ide --diff file1.txt file2.txt

# Launch the Antigravity Hub
antigravity
```

---

## 🔐 Security & GPG Verification

All packages and repository metadata are signed with the X3M Antigravity Packagers GPG key:
* **Fingerprint:** `E83A 23BC 57FE 6953 E4B5  F465 7A48 CA4D 7E7B 6601`
* **Public Key:** [RPM-GPG-KEY-antigravity](https://x3m-industries.github.io/antigravity-packages/RPM-GPG-KEY-antigravity)

---

## 🛠️ Development & Local Testing

This repository uses [mise](https://mise.jdx.dev/) to manage developer toolchains:

```bash
# Install toolchains defined in mise.toml
mise install

# Check upstream release status
python3 scripts/check_upstream.py
```

### Automation

* A GitHub Actions workflow runs daily at `05:00 UTC` to check Google's release page.
* When Google publishes a new version, the workflow automatically builds, signs, and releases new `.rpm` and `.deb` packages and updates the DNF/APT repositories.
* Can also be triggered manually at any time via **GitHub Actions > Build and Publish Packages > Run workflow**.
