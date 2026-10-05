#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Guards the GitHub Pages size limit (1 GB published site).
# If the APT pool (.deb files) is kept on Pages (KEEP_DEB_POOL=true), it dominates the site size.
# ==============================================================================

DIST_DIR="${1:-./dist}"
WARN_MB="${PAGES_WARN_MB:-700}"
FAIL_MB="${PAGES_FAIL_MB:-950}"

size_mb=$(du -sm "${DIST_DIR}" | cut -f1)
echo "GitHub Pages artifact size: ${size_mb} MB (warn at ${WARN_MB} MB, fail at ${FAIL_MB} MB; hard limit 1024 MB)"

if [ "${size_mb}" -ge "${FAIL_MB}" ]; then
    echo "Error: Pages artifact is ${size_mb} MB, too close to the 1 GB GitHub Pages limit." >&2
    echo "Set KEEP_DEB_POOL=false so APT downloads are served via https://apt.x3m.industries (see vercel-apt/)." >&2
    exit 1
fi

if [ "${size_mb}" -ge "${WARN_MB}" ]; then
    echo "::warning::Pages artifact is ${size_mb} MB; the 1 GB limit is approaching (APT pool is still kept on Pages; consider KEEP_DEB_POOL=false)."
fi
