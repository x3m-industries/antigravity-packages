# Reddit Distribution Strategy & Assets Guide

This directory contains 4 custom Reddit posts tailored for different subreddits, along with graphics designed specifically for Reddit's feed dimensions and developer audience.

---

## 📊 Post Matrix & Target Subreddits

| Post File | Strategic Angle | Primary Target Subreddits | Best Attached Graphic | Key Narrative Hook |
| :--- | :--- | :--- | :--- | :--- |
| **[`POST1.md`](./POST1.md)** | **Universal Suite & Desktop UX** | `r/AntigravityGoogle`<br>`r/GoogleAntigravityIDE`<br>`r/AntiGravityUsers`<br>`r/AntigravityIDE`<br>`r/google_antigravity` | `posts/assets/promo-card.png`<br>*(or `hero-banner.jpg`)* | Replaces tedious manual tarball unpacking with native DNF/APT repos, fixed OAuth browser redirects, and file manager right-click menus. |
| **[`POST2.md`](./POST2.md)** | **Packaging Architecture & Hardening** | `r/Fedora`<br>`r/linux`<br>`r/Ubuntu`<br>`r/debian` | `posts/assets/comparison-graphic.png` | Why tarballs fail on modern Linux (SUID `chrome-sandbox` permissions, AppArmor, SELinux) and how automated RPM/DEB repos solve it with GPG signing & CI smoke tests. |
| **[`POST3.md`](./POST3.md)** | **Terminal Hacker & CLI (`agy`)** | `r/GoogleAntigravityCLI`<br>`r/AntigravityCLI`<br>`r/antigravitymodels`<br>`r/commandline` | `posts/assets/cli-terminal-card.png` | Terminal-first experience: zero-sudo user-space install (`~/.local/bin/agy`), 15-min background auto-updater preserved, Bash/Zsh completions, and `agy`, `agy-ide`, `agy-hub` shortcuts. |
| **[`POST4.md`](./POST4.md)** | **Arch Linux & Rolling Releases** | `r/archlinux`<br>`r/arch`<br>`r/EndeavourOS`<br>`r/linuxquestions` | `posts/assets/promo-card.png`<br>*(or `comparison-graphic.png`)* | Respects Arch system hygiene: clean `debtap` package conversion for native `pacman` tracking, user-space CLI mode, and AUR PKGBUILD roadmap. |

---

## 🖼️ Included Graphics & Visuals (`posts/assets/`)

All graphics are rendered in **1200x675 (16:9)**, optimized for Reddit's desktop and mobile cards:

1. **`posts/assets/promo-card.png`**:
   - High-contrast developer card showing Antigravity IDE, Hub, and CLI icons.
   - Distro badges (Fedora, Ubuntu, Debian, Arch, openSUSE).
   - Highlighting the 1-command installer and core features (GPG signed, auto-sync, OAuth fixed, context menus).
2. **`posts/assets/comparison-graphic.png`**:
   - Visual comparison: "Raw Tarballs Unpacked to /opt" vs "X3M Native Linux Repositories".
   - Clear red crosses vs green checkmarks demonstrating security, updates, and desktop integration.
3. **`posts/assets/cli-terminal-card.png`**:
   - Sleek dark terminal mockup showing `agy`, prompt execution, and shortcuts (`agy-ide`, `agy-hub`).
   - Highlights user-space isolation (no sudo), auto-updates, and shell completions.
4. **`posts/assets/hero-banner.jpg`**:
   - AI-generated showcase illustration featuring the glowing Linux Tux surrounded by holographic Antigravity IDE / CLI nodes.

*(To regenerate the programmatic graphics at any time, run: `python3 scripts/generate_reddit_graphics.py`)*

---

## 🚀 Execution & Reddit Best Practices

### 1. Spacing Out Posts (Avoid Reddit Spam Filters)
- **Do NOT post to all 10+ subreddits in one hour.** Reddit’s automated filters flag accounts that blast identical or similar links across multiple subreddits simultaneously.
- **Recommended Schedule:**
  - **Day 1 (Round 1):** Post `POST1.md` to `r/AntigravityGoogle` and `POST2.md` to `r/Fedora`.
  - **Day 1 (Evening / 6 hours later):** Post `POST3.md` to `r/GoogleAntigravityCLI`.
  - **Day 2 (Round 2):** Post `POST4.md` to `r/archlinux` and `POST1.md` (with Option B title) to `r/GoogleAntigravityIDE`.
  - **Day 3 (Round 3):** Post variations to `r/AntiGravityUsers`, `r/AntigravityIDE`, and `r/AntigravityCLI`.

### 2. How to Create an "Image + Text" Post on Reddit
- On desktop Reddit, navigate to the target subreddit and click **Create Post**.
- Select the **Post** tab (rich text / markdown) or **Images & Video** tab.
- In modern Reddit desktop, the standard **Post** tab allows uploading an image inline at the top of the post or as a hero header with markdown text below it.
- Alternatively, on the official Reddit mobile app, create an Image post, add the picture, and paste the markdown content into the post description.

### 3. Engagement & Community Management
- **Pin / First Comment:** Often, adding a quick cordial comment right after posting helps jumpstart discussion:
  > *"Hey everyone! Maintainer here. Happy to answer any questions about the packaging pipeline, GPG verification, or distro-specific setups."*
- **Acknowledge Community Contributions:** If someone points out a distro edge case (e.g. openSUSE Tumbleweed or older Debian versions), offer to test and fix it. This turns skeptical commenters into loyal users and GitHub stargazers.
