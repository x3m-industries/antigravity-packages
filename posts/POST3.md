# Reddit Post 3: Terminal Hacker & CLI Power User Guide (`agy`)

> **Target Subreddits:**
> - `r/GoogleAntigravityCLI`
> - `r/AntigravityCLI`
> - `r/antigravitymodels`
> - `r/commandline`
>
> **Recommended Attached Graphic:**
> `posts/assets/cli-terminal-card.png`
>
> **Best Timing:**
> Midday or evening (15:00–21:00 UTC / 11:00–17:00 EST)

---

## 📌 Suggested Titles (Tailored for Terminal Users)

- **Option A (Feature-Dense & Practical - Recommended):**  
  `Google Antigravity CLI ('agy') on Linux: 1-command user-space install (no sudo), native 15-min auto-updates & shell completions`

- **Option B (Terminal Hacker Hook):**  
  `Terminal-first Google Antigravity: Running 'agy' with Bash/Zsh completions, zero root privileges, and instant shortcuts`

- **Option C (PSA Style):**  
  `PSA for Linux terminal users: How to install and manage the official Google Antigravity CLI without sudo or package conflicts`

---

## 📝 Post Body (Copy & Paste to Reddit)

*(Attach `cli-terminal-card.png` as the post image)*

If you’re using or experimenting with Google Antigravity, the official terminal coding agent **`agy`** is easily one of the best tools in the suite for fast, terminal-first pair programming, slash commands, and background task execution.

However, packaging a terminal CLI alongside desktop GUI applications (like the Antigravity IDE and Hub) presents a tricky dilemma on Linux:

1. **Root / Sudo Hazards:** CLI developer tools shouldn't require root privileges to install or run.
2. **Background Auto-Updater Breakage:** Google’s official `agy` binary includes a native background updater that checks for releases every 15 minutes during normal CLI sessions and self-updates in place. If a package manager forces `agy` into `/usr/bin/` as root, Google’s built-in self-updater fails with permission errors!
3. **`$PATH` Shadowing:** If someone runs Google's official install script alongside a third-party package, you risk version drift and broken symlinks.

### 💡 The Solution: Seamless User-Space Orchestration

We built our open-source packaging and installer infrastructure to handle `agy` cleanly and canonically:

- **Installed directly to `$HOME/.local/bin/agy`:** Requires **zero `sudo` privileges**.
- **100% Preserves Google's Native Auto-Updater:** Google’s background daemon self-updates seamlessly in user-space without permission hurdles.
- **Zero Collision Guarantee:** If you run Google’s official script (`curl -fsSL https://antigravity.google/cli/install.sh | bash`), it recognizes `~/.local/bin/agy` and exits cleanly.

---

### ⚡ 1-Command CLI Setup (No Sudo Required!)

To install **only** the CLI agent into user-space:

```bash
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --cli-only
```

*(Or run `curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash` to interactively install the full suite: IDE + Hub + CLI).*

🌐 **Documentation:** https://x3m-industries.github.io/antigravity-packages/  
⭐ **GitHub:** https://github.com/x3m-industries/antigravity-packages  

---

### ⌨️ Terminal Productivity Shortcuts

To make switching between the CLI, the code editor, and the hub frictionless, our tooling sets up ergonomic terminal aliases:

| Command | Target | Description | Scope |
| :--- | :--- | :--- | :--- |
| **`agy`** | CLI Terminal Agent | Official Google coding agent & pair programmer | User-space (`~/.local/bin/agy`) |
| **`agy-ide`** | Antigravity IDE | Instant shortcut to open current directory in IDE (`agy-ide .`) | System (`/usr/bin/agy-ide`) |
| **`agy-hub`** | Antigravity Hub | Launch the desktop agent hub / Antigravity 2.0 platform | System (`/usr/bin/agy-hub`) |

#### Shell Autocompletion (Bash & Zsh)
Tab completion is automatically configured for `antigravity-ide` and `agy-ide` under `/usr/share/bash-completion` and `/usr/share/zsh`.

---

### 🤖 Automation & Dotfiles Friendly

Setting up a fresh machine, container, or automated dotfiles? Use these headless flags:

```bash
# Silent unattended installation of complete suite (IDE + Hub + CLI)
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- -y

# Inspect installed components, versions, and repository health
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --status

# Print upstream Google tarball URLs & asset links directly
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --print-downloads

# Clean uninstallation (removes packages & repos without orphaned files)
curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --uninstall
```

If you live in the terminal and write code with `agy`, give it a spin and drop any thoughts or feature ideas below!
