#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Verifies that a directory contains the complete set of release packages:
#   {antigravity, antigravity-ide} x {x86_64/amd64, aarch64/arm64} x {rpm, deb}
# The RPM/APT repositories only reference the newest release, so a release that
# is missing any of these files would make packages vanish for users.
# ==============================================================================

PKG_DIR="${1:-./dist/packages}"

if [ ! -d "${PKG_DIR}" ]; then
    echo "Error: package directory '${PKG_DIR}' does not exist." >&2
    exit 1
fi

missing=0
require() {
    local pattern="$1"
    if ! compgen -G "${PKG_DIR}/${pattern}" > /dev/null; then
        echo "MISSING: ${pattern}" >&2
        missing=$((missing + 1))
    fi
}

for arch in x86_64 aarch64; do
    require "antigravity-[0-9]*.${arch}.rpm"
    require "antigravity-ide-[0-9]*.${arch}.rpm"
done
for arch in amd64 arm64; do
    require "antigravity_[0-9]*_${arch}.deb"
    require "antigravity-ide_[0-9]*_${arch}.deb"
done

if [ "${missing}" -gt 0 ]; then
    echo "Error: ${missing} expected package(s) missing from ${PKG_DIR}:" >&2
    ls -la "${PKG_DIR}" >&2
    exit 1
fi

echo "All 8 expected packages present in ${PKG_DIR}."
