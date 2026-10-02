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
            (
                cd "${DEB_DIR}" || exit 1
                dpkg-scanpackages --arch "${ARCH}" --multiversion pool/main > "dists/stable/main/binary-${ARCH}/Packages" 2>/dev/null || true
            )
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

# Copy GPG keys and assets to dist root
cp RPM-GPG-KEY-antigravity "${DIST_DIR}/"
cp antigravity.gpg "${DIST_DIR}/"
if compgen -G "google*.html" > /dev/null; then
    cp google*.html "${DIST_DIR}/"
fi
if [ -d "assets" ]; then
    cp -r assets "${DIST_DIR}/"
    cp assets/favicon.png "${DIST_DIR}/favicon.png" 2>/dev/null || true
fi

# Copy landing page template
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_DIR}")"
if [ -f "${REPO_ROOT}/templates/index.html" ]; then
    cp "${REPO_ROOT}/templates/index.html" "${DIST_DIR}/index.html"
elif [ -f "templates/index.html" ]; then
    cp "templates/index.html" "${DIST_DIR}/index.html"
fi

# Inject dynamic release versions into dist/index.html based on RELEASE_TAG
if [ -f "${DIST_DIR}/index.html" ] && [ -n "${RELEASE_TAG:-}" ] && [ "${RELEASE_TAG}" != "latest" ] && [ "${RELEASE_TAG}" != "vlatest" ]; then
    if [ -f "${SCRIPT_DIR}/inject_versions.py" ]; then
        python3 "${SCRIPT_DIR}/inject_versions.py" "${RELEASE_TAG}" "${DIST_DIR}/index.html" || true
    fi
fi

# Copy universal installer script
if [ -f "${REPO_ROOT}/install.sh" ]; then
    cp "${REPO_ROOT}/install.sh" "${DIST_DIR}/install.sh"
elif [ -f "install.sh" ]; then
    cp "install.sh" "${DIST_DIR}/install.sh"
fi

# Generate robots.txt
cat << 'ROBOTS_EOF' > "${DIST_DIR}/robots.txt"
User-agent: *
Allow: /

Sitemap: https://x3m-industries.github.io/antigravity-packages/sitemap.xml
ROBOTS_EOF

# Generate sitemap.xml
CURRENT_DATE=$(date -u +"%Y-%m-%d")
cat << SITEMAP_EOF > "${DIST_DIR}/sitemap.xml"
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://x3m-industries.github.io/antigravity-packages/</loc>
    <lastmod>${CURRENT_DATE}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
SITEMAP_EOF

echo "Repository generation complete."
