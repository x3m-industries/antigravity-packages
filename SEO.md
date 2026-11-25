# SEO Strategy & Search Growth Playbook (`SEO.md`)

This document defines the long-term, data-driven SEO architecture for **`antigravity-packages`** (`https://x3m-industries.github.io/antigravity-packages/`). It is designed as a persistent cross-session playbook so maintainers and AI development agents make coordinated, compounding improvements instead of ad-hoc meta tweaks.

---

## 1. Strategic Diagnosis & Baseline Metrics

### Baseline Snapshot — `2026-11-25` (Google Search Console, Last 3 Months: 2026-09-10 to 2026-11-23)

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Total Impressions** | **4,509** | Accelerating strongly: ~10/day (Sep) → ~80/day (Oct) → **130–143/day** (Nov 20–23) |
| **Total Clicks** | **29** | `17` on `/` (`0.74%` CTR), `12` on `/docs.html` (`0.51%` CTR) |
| **Overall CTR** | **0.64%** | Primary bottleneck — rankings are already Page 1 |
| **Average Position** | **8.1** | `/` at `7.87`, `/docs.html` at `8.66` |
| **Device Split** | **94.4% Desktop** | Desktop: 4,255 impr (27 clicks); Mobile: 246 impr (2 clicks); Tablet: 8 impr |
| **Rich Search Appearances** | **0** | Google shows plain blue links — `<title>`, `<meta description>`, and URL slug drive nearly 100% of CTR |
| **Top Geographies (Impressions)** | US (566), IN (545), BR (352), ID (264), DE (229), RU (158), UK (135), IT (111), PL (106), VN (102) | Strongly global developer audience |

### High-Impression Query Clusters (Baseline)

| Priority | Intent Cluster | Est. Impressions | Avg Pos | Baseline Clicks | Representative Queries |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **P0** | **Arch Linux / `pacman` / `agy` CLI** | **~580+** | 7.4–9.5 | **0** | `antigravity cli arch` (169), `arch antigravity cli` (56), `antigravity arch` (53), `antigravity cli arch linux` (44), `pacman antigravity` (43), `antigravity pacman` (34), `agy cli arch` (10 @ pos 5.9), `yay antigravity`, `antigravity for cachyos` |
| **P1** | **Uninstall on Ubuntu / Linux** | **~70+** | 6.6–9.5 | **0** | `uninstall antigravity ubuntu` (23 @ pos 6.65), `how to uninstall antigravity from ubuntu` (18), `how to uninstall antigravity ubuntu` (9), `remove antigravity completely ubuntu` |
| **P2** | **openSUSE (Zypper / Tumbleweed / Leap)** | **~16+** | 5.5 | **0** | `antigravity opensuse` (13 @ pos 5.54), `tumbleweed`, `leap 16.1` |
| **P3** | **Fedora / RHEL / RPM (DNF)** | **~30+** | 7.2–9.7 | **1** | `antigravity fedora` (8), `fedora antigravity` (7), `agy fedora` (4), `antigravity rpm` (3), `install antigravity fedora` (1 click) |
| **P4** | **Ubuntu / Debian / Mint (APT)** | **~25+** | 5.0–11.0 | **1** | `install antigravity debian` (3 @ pos 5.0), `antigravity for linux mint` (3), `sudo apt update antigravity`, `how to update antigravity ide in ubuntu`, `antigravity ubuntu 26.04` |

### Root Cause of Low CTR (`0.64%`)
1. **Intent dilution (2-page bottleneck):** Only 2 URLs (`/` and `/docs.html`) were indexed to serve 5+ completely distinct developer intents.
2. **Kitchen-sink titles:** `docs.html` crammed `Arch, APT, DNF, CLI & Uninstall` into a single title, losing relevance and getting truncated in SERPs against single-purpose results (Reddit threads, blog posts, AUR pages).
3. **Missing high-demand keywords in dedicated titles:** Neither `/` nor `docs.html` led with `Arch Linux`, `pacman`, `Uninstall Ubuntu`, or `openSUSE Zypper`.

---

## 2. Hub-and-Spoke URL Architecture (Anti-Cannibalization Map)

Every URL owns **one primary search intent**. Do **not** let two pages compete for the exact same primary title/H1.

| URL | Role | Primary Target Queries | Target `<title>` (50–62 chars) |
| :--- | :--- | :--- | :--- |
| `/` (`index.html`) | **Suite Hub** | `google antigravity linux`, `antigravity linux packages`, `download antigravity linux`, `install antigravity 2.0 linux` | `Google Antigravity for Linux — RPM, DEB, Arch & CLI (agy)` |
| `/arch.html` | **P0 Spoke (Arch)** | `antigravity cli arch`, `pacman antigravity`, `antigravity arch linux`, `agy arch`, `cachyos`, `manjaro`, `PKGBUILD` | `Install Antigravity & CLI (agy) on Arch Linux (pacman/PKGBUILD)` |
| `/uninstall.html` | **P1 Spoke (Uninstall)** | `uninstall antigravity ubuntu`, `how to uninstall antigravity from ubuntu`, `remove antigravity completely ubuntu`, `uninstall antigravity linux` | `How to Uninstall Google Antigravity on Ubuntu & Linux` |
| `/opensuse.html` | **P2 Spoke (openSUSE)** | `antigravity opensuse`, `opensuse zypper antigravity`, `tumbleweed`, `leap 15/16` | `Install Google Antigravity on openSUSE (Tumbleweed & Leap)` |
| `/fedora.html` | **P3 Spoke (Fedora/RPM)** | `antigravity fedora`, `install antigravity fedora`, `agy fedora`, `google antigravity rpm`, `antigravity rpm repository` | `Install Google Antigravity on Fedora, RHEL & Rocky (DNF RPM)` |
| `/ubuntu.html` | **P4 Spoke (Ubuntu/APT)** | `install antigravity ubuntu`, `install antigravity debian`, `antigravity linux mint`, `ubuntu 26.04`, `how to update antigravity ide in ubuntu` | `Install & Update Google Antigravity on Ubuntu, Debian & Mint` |
| `/docs.html` | **Reference Hub** | `antigravity install.sh flags`, `antigravity nautilus`, `antigravity gpg key`, `chrome-sandbox suid ubuntu` | `Antigravity Linux Docs — CLI Flags, GPG Keys & Integrations` |

### Internal Linking Rules
1. **Homepage (`/`):** The Distro Quick-Anchors Bar directly links to `arch.html`, `ubuntu.html`, `fedora.html`, `opensuse.html`, and `uninstall.html` (real URLs, not `#hash` fragments on `docs.html`).
2. **Global Footer:** Every page links to the full hub-and-spoke cluster so PageRank distributes evenly and Google discovers every URL within 1 hop.
3. **Subpage Navbar:** Guide pages share compact cross-links (`← Quickstart`, `Arch`, `Ubuntu`, `Fedora`, `openSUSE`, `Uninstall`, `Docs`).
4. **Canonical root links:** Always link to `/antigravity-packages/` (`siteConfig.baseUrl`), never `index.html`.
5. **Sitemap parity:** `scripts/generate_repos.sh` MUST list every public `.html` page in `sitemap.xml` with current UTC `<lastmod>`.

---

## 3. Technical SEO Guardrails (For All Future Agent Sessions)

Before merging any change touching `site/`, `templates/`, or `scripts/generate_repos.sh`, verify:

- [ ] **Flat file build:** `site/astro.config.mjs` keeps `build.format: 'file'` (outputs `/<slug>.html` cleanly on GitHub Pages).
- [ ] **Unique metadata per page:** Every page passes explicit `title`, `description` (135–160 chars, action-oriented, copy-paste promise), `canonicalUrl`, `breadcrumbLabel`, page-specific `faqs`, and page-specific `howTo` to `BaseLayout.astro`.
- [ ] **Clean JSON-LD:** No raw HTML tags or `&amp;` entities inside `<script type="application/ld+json">` (guarded by `tests/test_packaging.py`).
- [ ] **Live version injection:** Every page referencing release versions uses `currentVersions` from `siteConfig.ts` (and `scripts/generate_repos.sh` runs `inject_versions.py` over `${DIST_DIR}/*.html`).
- [ ] **Fast above-the-fold answers:** Put the exact copy-pasteable command in the very first card above the fold (developers bounce immediately if forced to scroll past marketing fluff).
- [ ] **Conversion telemetry (GA4):** Every code block uses `copyCode(this)` so we measure copy-to-clipboard conversion rates per landing page (`copy_docs_command` + section/page labels).
- [ ] **AI / LLM Search parity:** Keep `llms.txt` and `llms-full.txt` updated with the canonical URLs of all dedicated guide pages so Perplexity, ChatGPT Search, Gemini, and Claude cite the exact distro page.
- [ ] **Zero stale URLs:** Client-facing repo URLs MUST use `https://rpm.x3m.industries/rpm/` (RPM/DNF/Zypper) and `https://apt.x3m.industries/deb` (DEB/APT), never raw `github.io` repo paths.

---

## 4. Phased Roadmap & KPI Targets

### Phase 1 — Hub-and-Spoke Launch (Completed `2026-11-25`)
- Ship dedicated Astro pages: `arch.html`, `uninstall.html`, `opensuse.html`, `fedora.html`, `ubuntu.html`.
- De-clutter `/` and `docs.html` titles & descriptions.
- Upgrade `BaseLayout.astro` for per-page canonical, BreadcrumbList, FAQPage, and HowTo JSON-LD.
- Expand `sitemap.xml` in `scripts/generate_repos.sh` to include all 7 URLs and update `llms.txt`.

### Phase 2 — 30-Day Review (`~2026-12-25`)
Drop a fresh 28-day GSC export into `tmp/` and compare against the `2026-11-25` baseline:
- **Target KPIs (30–60 days post-launch):**
  - `arch.html`: avg position `< 5.0`, CTR `>= 4%`
  - `uninstall.html`: avg position `< 4.5`, CTR `>= 5%`
  - `opensuse.html`: avg position `< 4.0`, CTR `>= 4%`
  - Site-wide CTR: `0.64%` → **`2.5%–4.0%+`** (4–6x click growth on existing impression volume)
- **Actions based on 30-day data:**
  - Identify any query with `>= 20` impressions and `< 1%` CTR → rewrite that page's `<title>` and `<meta description>` to mirror exact searcher phrasing.
  - Check `Pages.csv` to verify all 7 URLs are indexed in Google Search Console (submit `sitemap.xml` manually in GSC if any page is still "Discovered – currently not indexed").

### Phase 3 — Product-Led SEO Expansion (60–90 Days)
1. **Publish official AUR packages (`antigravity-ide-bin` & `antigravity-bin`):** Queries like `pacman antigravity` (43), `antigravity pacman` (34), `yay antigravity`, and `aur antigravity ide` show strong Arch demand. Publishing automated AUR packages (updated by GitHub Actions alongside GitHub Releases) turns `arch.html` into an authoritative `yay -S antigravity-ide-bin` destination AND drives high-authority backlinks from `aur.archlinux.org`.
2. **Troubleshooting long-tail pages (only if GSC shows >= 30 impr/month):**
   - `chrome-sandbox` SUID error on Ubuntu 24.04 / 26.04
   - Google OAuth redirect (`antigravity-ide://` / `antigravity://`) on Linux
   - Upgrading/migrating from manual `/opt` tarball extractions
3. **Internationalization check:** Monitor non-English queries (`desinstalar antigravity`, `instalar en cachyos`, `я на арче`, `gpg: nenhum dado openpgp`) — keep commands clean and scannable since developers worldwide convert well on clear English command blocks.

---

## 5. Change Log & Measurement History

| Date | Change / Snapshot | Key Metrics / Notes |
| :--- | :--- | :--- |
| `2026-11-25` | Baseline GSC export recorded (90d: Sep 10 – Nov 23) + Phase 1 hub-and-spoke rollout (`arch.html`, `uninstall.html`, `opensuse.html`, `fedora.html`, `ubuntu.html`, updated `sitemap.xml` & `llms.txt`) | Baseline: 4,509 impr, 29 clicks, 0.64% CTR, pos 8.1 (130–143 impr/day late Nov) |
