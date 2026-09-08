#!/usr/bin/env bash
set -euo pipefail

RELEASE_TAG="${1:-latest}"
DIST_DIR="${2:-./dist}"

RPM_DIR="${DIST_DIR}/rpm"
DEB_DIR="${DIST_DIR}/deb"
PKG_DIR="${DIST_DIR}/packages"

mkdir -p "${RPM_DIR}" "${DEB_DIR}"

echo "=== Generating RPM Repository Metadata ==="
createrepo_c -u "https://github.com/x3m-industries/antigravity-packages/releases/download/${RELEASE_TAG}/" "${RPM_DIR}"

# Copy RPM GPG public key
cp RPM-GPG-KEY-antigravity "${RPM_DIR}/"

# Generate client .repo file
cat << REPO_EOF > "${RPM_DIR}/antigravity.repo"
[antigravity]
name=Antigravity Packages Repository
baseurl=https://x3m-industries.github.io/antigravity-packages/rpm/
enabled=1
gpgcheck=1
gpgkey=https://x3m-industries.github.io/antigravity-packages/rpm/RPM-GPG-KEY-antigravity
REPO_EOF

echo "=== Generating DEB Repository Metadata ==="
DEB_POOL="${DEB_DIR}/pool/main"
mkdir -p "${DEB_POOL}"

if compgen -G "${PKG_DIR}/*.deb" > /dev/null; then
    cp "${PKG_DIR}"/*.deb "${DEB_POOL}/"
    
    if command -v dpkg-scanpackages > /dev/null 2>&1; then
        for ARCH in amd64 arm64; do
            DISTS_ARCH="${DEB_DIR}/dists/stable/main/binary-${ARCH}"
            mkdir -p "${DISTS_ARCH}"
            (cd "${DEB_DIR}" && dpkg-scanpackages --arch "${ARCH}" --multiversion pool/main > "dists/stable/main/binary-${ARCH}/Packages" 2>/dev/null || true)
            if [ -s "${DISTS_ARCH}/Packages" ]; then
                gzip -9c "${DISTS_ARCH}/Packages" > "${DISTS_ARCH}/Packages.gz"
            fi
        done
        
        # Generate Release file
        cat << REL_EOF > "${DEB_DIR}/dists/stable/Release"
Origin: X3M Industries
Label: Antigravity Packages
Suite: stable
Codename: stable
Components: main
Architectures: amd64 arm64
Description: Apt repository for Google Antigravity & Antigravity IDE
Date: $(date -Ru)
REL_EOF

        # Sign Release file if GPG is available
        if gpg --list-secret-keys "packaging@x3m.industries" > /dev/null 2>&1; then
            gpg --batch --yes -u "packaging@x3m.industries" --armor --detach-sign --output "${DEB_DIR}/dists/stable/Release.gpg" "${DEB_DIR}/dists/stable/Release"
            gpg --batch --yes -u "packaging@x3m.industries" --clearsign --output "${DEB_DIR}/dists/stable/InRelease" "${DEB_DIR}/dists/stable/Release"
        fi
    fi
fi

# Copy GPG keys to DEB root
cp antigravity.gpg "${DEB_DIR}/"
cp RPM-GPG-KEY-antigravity "${DEB_DIR}/antigravity.asc"

# Generate modern DEB822 source file
cat << DEB822_EOF > "${DEB_DIR}/antigravity.sources"
Types: deb
URIs: https://x3m-industries.github.io/antigravity-packages/deb
Suites: stable
Components: main
Signed-By: /etc/apt/keyrings/antigravity.gpg
DEB822_EOF

# Generate traditional .list file
cat << LIST_EOF > "${DEB_DIR}/antigravity.list"
deb [signed-by=/etc/apt/keyrings/antigravity.gpg] https://x3m-industries.github.io/antigravity-packages/deb stable main
LIST_EOF

# Copy GPG keys to dist root
cp RPM-GPG-KEY-antigravity "${DIST_DIR}/"
cp antigravity.gpg "${DIST_DIR}/"

# Modern, stunning Antigravity-styled landing page
cat << 'HTML_EOF' > "${DIST_DIR}/index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Antigravity Linux Repositories | X3M Industries</title>
    <meta name="description" content="Community RPM and DEB repositories for Google Antigravity & Antigravity IDE.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(18, 24, 38, 0.7);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.25);
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.2);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --code-bg: #070a12;
            --success: #10b981;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 85% 25%, rgba(56, 189, 248, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 50% 80%, rgba(168, 85, 247, 0.08) 0%, transparent 50%);
            background-attachment: fixed;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 48px 24px 80px;
        }

        header {
            text-align: center;
            margin-bottom: 48px;
        }

        .logo-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: var(--accent);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
            letter-spacing: 0.02em;
        }

        h1 {
            font-size: clamp(2.2rem, 5vw, 3.2rem);
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.03em;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 1.15rem;
            color: var(--text-muted);
            max-width: 640px;
            margin: 0 auto 28px;
        }

        .badges-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: var(--text-main);
        }

        .badge.highlight {
            background: rgba(16, 185, 129, 0.12);
            border-color: rgba(16, 185, 129, 0.3);
            color: var(--success);
        }

        /* Tabs */
        .tabs-wrapper {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 28px;
            backdrop-filter: blur(12px);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
            margin-bottom: 40px;
        }

        .tab-buttons {
            display: flex;
            gap: 8px;
            background: rgba(0, 0, 0, 0.3);
            padding: 4px;
            border-radius: 12px;
            margin-bottom: 24px;
        }

        .tab-btn {
            flex: 1;
            padding: 10px 16px;
            border: none;
            background: transparent;
            color: var(--text-muted);
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab-btn.active {
            background: var(--primary);
            color: #ffffff;
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .step-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--accent);
            font-weight: 700;
            margin-bottom: 8px;
        }

        .code-block {
            position: relative;
            background: var(--code-bg);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            padding: 16px 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: #e2e8f0;
            overflow-x: auto;
            margin-bottom: 20px;
        }

        .code-block code {
            display: block;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.2s;
        }

        .copy-btn:hover {
            background: rgba(255, 255, 255, 0.15);
            color: #fff;
        }

        /* Feature Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .feature-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }

        .feature-card h3 {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .feature-card p {
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        footer {
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            padding-top: 24px;
            border-top: 1px solid var(--card-border);
        }

        footer a {
            color: var(--accent);
            text-decoration: none;
            transition: color 0.2s;
        }

        footer a:hover {
            color: #fff;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-badge">
                <span>✦</span> X3M Industries Community Distribution
            </div>
            <h1>Google Antigravity for Linux</h1>
            <p class="subtitle">
                Automated native RPM and DEB repositories for Antigravity IDE and Antigravity Hub, synchronized with Google's official releases.
            </p>
            <div class="badges-row">
                <span class="badge highlight">● Fully Automated</span>
                <span class="badge">x86_64 &amp; aarch64</span>
                <span class="badge">GPG Signed</span>
                <span class="badge">OAuth Callback Ready</span>
            </div>
        </header>

        <div class="tabs-wrapper">
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="switchTab('rpm')">Fedora / RHEL / Rocky (DNF)</button>
                <button class="tab-btn" onclick="switchTab('deb')">Ubuntu / Debian / Mint (APT)</button>
            </div>

            <!-- RPM Tab -->
            <div id="rpm" class="tab-content active">
                <div class="step-label">Step 1 — Add the RPM repository</div>
                <div class="code-block">
                    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                    <code>sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo</code>
                </div>

                <div class="step-label">Step 2 — Install Antigravity IDE &amp; Hub</div>
                <div class="code-block">
                    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                    <code>sudo dnf install antigravity-ide antigravity</code>
                </div>

                <div class="step-label">Step 3 — Launch from terminal</div>
                <div class="code-block">
                    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                    <code>antigravity-ide ./myproject</code>
                </div>
            </div>

            <!-- DEB Tab -->
            <div id="deb" class="tab-content">
                <div class="step-label">Step 1 — Add GPG Key &amp; Sources</div>
                <div class="code-block">
                    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                    <code>sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources</code>
                </div>

                <div class="step-label">Step 2 — Install via APT</div>
                <div class="code-block">
                    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                    <code>sudo apt update &amp;&amp; sudo apt install antigravity-ide antigravity</code>
                </div>

                <div class="step-label">Step 3 — Launch from terminal</div>
                <div class="code-block">
                    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                    <code>antigravity-ide ./myproject</code>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="feature-card">
                <h3>⚡ Zero Maintenance</h3>
                <p>Tracked daily against Google's download CDN. Whenever a new version is released, the pipeline builds, signs, and updates the repositories automatically.</p>
            </div>
            <div class="feature-card">
                <h3>🖥️ Native Desktop &amp; CLI</h3>
                <p>Includes high-resolution icons, FreeDesktop menu entries, full CLI arguments (<code>antigravity-ide .</code>), and browser OAuth callback handlers (<code>antigravity-ide://</code>).</p>
            </div>
            <div class="feature-card">
                <h3>🔐 GPG Signed &amp; Secure</h3>
                <p>Every package is cryptographically signed with the X3M Antigravity Packagers key, ensuring package authenticity and integrity across all systems.</p>
            </div>
        </div>

        <footer>
            <p>Maintained with pride by <a href="https://github.com/x3m-industries" target="_blank">X3M Industries</a> · <a href="https://github.com/x3m-industries/antigravity-packages" target="_blank">View GitHub Repository</a></p>
        </footer>
    </div>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }

        function copyCode(btn) {
            const code = btn.nextElementSibling.innerText;
            navigator.clipboard.writeText(code).then(() => {
                const originalText = btn.innerText;
                btn.innerText = 'Copied!';
                btn.style.color = '#10b981';
                setTimeout(() => {
                    btn.innerText = originalText;
                    btn.style.color = '';
                }, 2000);
            });
        }
    </script>
</body>
</html>
HTML_EOF

echo "Repository generation complete."
