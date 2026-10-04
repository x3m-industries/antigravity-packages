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

for pkg in "${PKG_DIR}"/*.rpm; do
    [ -e "${pkg}" ] || continue
    echo "Inspecting RPM: $(basename "${pkg}")..."
    if command -v rpm > /dev/null 2>&1; then
        rpm -qpi "${pkg}" > /dev/null
        if rpm -qlp "${pkg}" 2>/dev/null | grep -q "chrome-sandbox"; then
            perms=$(rpm -qlvp "${pkg}" 2>/dev/null | grep "chrome-sandbox" | awk '{print $1}')
            if [[ "$perms" == *"-rwsr-xr-x"* ]]; then
                echo "  ✓ chrome-sandbox packaged with SUID mode 4755 (-rwsr-xr-x)"
            else
                echo "ERROR: chrome-sandbox in ${pkg} does not have SUID mode 4755 (found ${perms})" >&2
                exit 1
            fi
        fi
    fi
done

for pkg in "${PKG_DIR}"/*.deb; do
    [ -e "${pkg}" ] || continue
    echo "Inspecting DEB: $(basename "${pkg}")..."
    if command -v dpkg-deb > /dev/null 2>&1; then
        dpkg-deb -I "${pkg}" > /dev/null
        tmp_ctrl=$(mktemp -d)
        if dpkg-deb -e "${pkg}" "${tmp_ctrl}" 2>/dev/null; then
            if [ -f "${tmp_ctrl}/postinst" ] && grep -q "chmod 4755" "${tmp_ctrl}/postinst"; then
                echo "  ✓ deb postinst configures SUID permissions (chmod 4755)"
            fi
            rm -rf "${tmp_ctrl}"
        fi
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
            for b in /usr/bin/antigravity /usr/bin/antigravity-ide /usr/bin/agy-ide /usr/bin/agy-hub; do
                if [ -e "$b" ]; then
                    test -x "$b"
                    echo "  ✓ $b is executable"
                fi
            done

            echo "Verifying desktop integration..."
            for d in /usr/share/applications/antigravity.desktop /usr/share/applications/antigravity-ide.desktop /usr/share/applications/antigravity-ide-url-handler.desktop; do
                if [ -e "$d" ]; then
                    echo "  ✓ $d installed"
                fi
            done

            echo "Verifying chrome-sandbox SUID permissions..."
            for cs in /usr/share/antigravity/chrome-sandbox /usr/share/antigravity-ide/chrome-sandbox; do
                if [ -f "$cs" ]; then
                    perms=$(stat -c "%a" "$cs")
                    if [ "$perms" != "4755" ]; then
                        echo "ERROR: $cs has permissions $perms, expected 4755" >&2
                        exit 1
                    fi
                    echo "  ✓ $cs has correct SUID permissions (4755)"
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
            for b in /usr/bin/antigravity /usr/bin/antigravity-ide /usr/bin/agy-ide /usr/bin/agy-hub; do
                if [ -e "$b" ]; then
                    test -x "$b"
                    echo "  ✓ $b is executable"
                fi
            done

            echo "Verifying desktop integration..."
            for d in /usr/share/applications/antigravity.desktop /usr/share/applications/antigravity-ide.desktop /usr/share/applications/antigravity-ide-url-handler.desktop; do
                if [ -e "$d" ]; then
                    echo "  ✓ $d installed"
                fi
            done

            echo "Verifying chrome-sandbox SUID permissions..."
            for cs in /usr/share/antigravity/chrome-sandbox /usr/share/antigravity-ide/chrome-sandbox; do
                if [ -f "$cs" ]; then
                    perms=$(stat -c "%a" "$cs")
                    if [ "$perms" != "4755" ]; then
                        echo "ERROR: $cs has permissions $perms, expected 4755" >&2
                        exit 1
                    fi
                    echo "  ✓ $cs has correct SUID permissions (4755)"
                fi
            done

            echo "DEB installation smoke test PASSED!"
        '
fi

echo -e "\n=== All Package Smoke Tests Completed Successfully! ==="
