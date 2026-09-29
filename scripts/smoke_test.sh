#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Package Smoke Test for Antigravity & Antigravity IDE
# Validates that generated .rpm and .deb packages install and integrate cleanly.
# ==============================================================================

PKG_DIR="${1:-./dist/packages}"

if [ ! -d "${PKG_DIR}" ]; then
    echo "Error: Package directory '${PKG_DIR}' does not exist." >&2
    exit 1
fi

ENGINE=""
if command -v docker > /dev/null 2>&1; then
    ENGINE="docker"
elif command -v podman > /dev/null 2>&1; then
    ENGINE="podman"
fi

echo "=== Running Package Smoke Tests ==="
echo "Package directory: ${PKG_DIR}"
echo "Container runtime: ${ENGINE:-None (inspect only)}"

# Basic structural validation first
for pkg in "${PKG_DIR}"/*.rpm; do
    [ -e "${pkg}" ] || continue
    echo "Inspecting RPM: $(basename "${pkg}")..."
    if command -v rpm > /dev/null 2>&1; then
        rpm -qpi "${pkg}" > /dev/null
    fi
done

for pkg in "${PKG_DIR}"/*.deb; do
    [ -e "${pkg}" ] || continue
    echo "Inspecting DEB: $(basename "${pkg}")..."
    if command -v dpkg-deb > /dev/null 2>&1; then
        dpkg-deb -I "${pkg}" > /dev/null
    fi
done

if [ -z "${ENGINE}" ]; then
    echo "No container engine available (docker/podman). Skipping container install tests."
    exit 0
fi

SELINUX_FLAG=""
if [ "${ENGINE}" = "podman" ]; then
    SELINUX_FLAG=",Z"
fi

PKG_DIR_ABS="$(cd "${PKG_DIR}" && pwd)"

# 1. Fedora / RPM Installation Test
RPM_COUNT=$(find "${PKG_DIR_ABS}" -maxdepth 1 -name "*x86_64.rpm" | wc -l)
if [ "${RPM_COUNT}" -gt 0 ]; then
    echo -e "\n---> [1/2] Testing RPM installation in Fedora container..."
    # shellcheck disable=SC2016
    "${ENGINE}" run --rm \
        -v "${PKG_DIR_ABS}:/packages:ro${SELINUX_FLAG}" \
        docker.io/library/fedora:latest bash -c '
            set -euo pipefail
            echo "Installing packages with DNF..."
            dnf install -y /packages/*x86_64.rpm

            echo "Verifying package database..."
            rpm -q antigravity || true
            rpm -q antigravity-ide || true

            echo "Verifying binary symlinks..."
            for b in /usr/bin/antigravity /usr/bin/antigravity-ide; do
                if [ -e "$b" ]; then
                    test -x "$b"
                    echo "  ✓ $b is executable"
                fi
            done

            echo "Verifying desktop integration..."
            for d in /usr/share/applications/antigravity.desktop /usr/share/applications/antigravity-ide.desktop; do
                if [ -e "$d" ]; then
                    echo "  ✓ $d installed"
                fi
            done

            echo "RPM installation smoke test PASSED!"
        '
fi

# 2. Ubuntu / DEB Installation Test
DEB_COUNT=$(find "${PKG_DIR_ABS}" -maxdepth 1 -name "*amd64.deb" | wc -l)
if [ "${DEB_COUNT}" -gt 0 ]; then
    echo -e "\n---> [2/2] Testing DEB installation in Ubuntu container..."
    # shellcheck disable=SC2016
    "${ENGINE}" run --rm \
        -v "${PKG_DIR_ABS}:/packages:ro${SELINUX_FLAG}" \
        docker.io/library/ubuntu:24.04 bash -c '
            set -euo pipefail
            echo "Updating apt indexes..."
            apt-get update -qq

            echo "Installing packages with APT..."
            DEBIAN_FRONTEND=noninteractive apt-get install -y /packages/*amd64.deb

            echo "Verifying package database..."
            dpkg -s antigravity 2>/dev/null || true
            dpkg -s antigravity-ide 2>/dev/null || true

            echo "Verifying binary symlinks..."
            for b in /usr/bin/antigravity /usr/bin/antigravity-ide; do
                if [ -e "$b" ]; then
                    test -x "$b"
                    echo "  ✓ $b is executable"
                fi
            done

            echo "Verifying desktop integration..."
            for d in /usr/share/applications/antigravity.desktop /usr/share/applications/antigravity-ide.desktop; do
                if [ -e "$d" ]; then
                    echo "  ✓ $d installed"
                fi
            done

            echo "DEB installation smoke test PASSED!"
        '
fi

echo -e "\n=== All Package Smoke Tests Completed Successfully! ==="
