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

# Root landing page for GitHub Pages
cat << 'HTML_EOF' > "${DIST_DIR}/index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Antigravity Linux Repositories (X3M Industries)</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 820px; margin: 40px auto; padding: 0 20px; color: #24292e; }
        pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; border: 1px solid #e1e4e8; }
        code { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }
        h1, h2 { border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
        .badge { display: inline-block; background: #0366d6; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; margin-right: 6px; }
    </style>
</head>
<body>
    <h1>Google Antigravity & Antigravity IDE Packages</h1>
    <p>Automated RPM (DNF) and DEB (APT) repositories for Google Antigravity, maintained by <strong>X3M Industries</strong>.</p>
    <div>
        <span class="badge">x86_64</span>
        <span class="badge">aarch64 / arm64</span>
        <span class="badge">GPG-Signed</span>
    </div>

    <h2>Fedora / RHEL / Rocky / AlmaLinux / CentOS (RPM)</h2>
    <p>Add the repository to DNF:</p>
    <pre><code>sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo
sudo dnf install antigravity-ide antigravity</code></pre>

    <h2>Ubuntu / Debian / Linux Mint / Pop!_OS (DEB)</h2>
    <p>Add the repository to APT:</p>
    <pre><code>sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
sudo curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources
sudo apt update
sudo apt install antigravity-ide antigravity</code></pre>

    <h2>CLI Usage</h2>
    <p>Launch from anywhere:</p>
    <pre><code>antigravity-ide ./myproject
antigravity</code></pre>

    <p><a href="https://github.com/x3m-industries/antigravity-packages">View on GitHub</a></p>
</body>
</html>
HTML_EOF

echo "Repository generation complete."
