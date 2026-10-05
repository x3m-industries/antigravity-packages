#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Package Smoke Test for Antigravity & Antigravity IDE
# Validates that generated .rpm and .deb packages install and integrate cleanly.
#
# Usage: smoke_test.sh [PKG_DIR]
# Env:   SMOKE_ARCH=x86_64|aarch64  Architecture to test (default: host arch).
#                                   Non-native arches run through QEMU emulation
#                                   (e.g. docker/setup-qemu-action in CI).
# ==============================================================================

PKG_DIR="${1:-./dist/packages}"

if [ ! -d "${PKG_DIR}" ]; then
    echo "Error: Package directory '${PKG_DIR}' does not exist." >&2
    exit 1
fi

case "${SMOKE_ARCH:-$(uname -m)}" in
    x86_64|amd64)  RPM_ARCH="x86_64";  DEB_ARCH="amd64"; PLATFORM="linux/amd64" ;;
    aarch64|arm64) RPM_ARCH="aarch64"; DEB_ARCH="arm64"; PLATFORM="linux/arm64" ;;
    *) echo "Error: unsupported SMOKE_ARCH '${SMOKE_ARCH:-$(uname -m)}'." >&2; exit 1 ;;
esac

ENGINE=""
if command -v docker > /dev/null 2>&1; then
    ENGINE="docker"
elif command -v podman > /dev/null 2>&1; then
    ENGINE="podman"
fi

echo "=== Running Package Smoke Tests (${RPM_ARCH}) ==="
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

# Which apps are present for this architecture decides what must be installed and verified
has_pkg() { compgen -G "${PKG_DIR_ABS}/$1" > /dev/null; }

# Shared in-container verification. Every expected file is REQUIRED: a missing binary,
# desktop entry or unresolved shared library fails the smoke test.
read -r -d '' VERIFY_COMMON <<'VERIFY_EOF' || true
fail() { echo "ERROR: $*" >&2; exit 1; }

verify_app() {
    local name="$1" bin="$2" short="$3" desktop="$4" dir="/usr/share/$1"

    test -x "$bin" || fail "$bin is missing or not executable"
    echo "  ✓ $bin is executable"
    test -x "$short" || fail "$short is missing or not executable"
    echo "  ✓ $short is executable"
    test -e "/usr/share/applications/$desktop" || fail "/usr/share/applications/$desktop not installed"
    echo "  ✓ /usr/share/applications/$desktop installed"

    echo "Verifying chrome-sandbox SUID permissions ($name)..."
    cs="$dir/chrome-sandbox"
    if [ -f "$cs" ]; then
        perms=$(stat -c "%a" "$cs")
        if [ "$perms" != "4755" ]; then
            echo "ERROR: $cs has permissions $perms, expected 4755" >&2
            exit 1
        fi
        echo "  ✓ $cs has correct SUID permissions (4755)"
    fi

    echo "Verifying shared libraries resolve ($name)..."
    command -v ldd > /dev/null 2>&1 || fail "ldd not available in container"
    bad=0
    while IFS= read -r f; do
        head -c 4 "$f" | grep -aq "ELF" || continue
        unresolved=$(ldd "$f" 2>/dev/null | grep "not found" || true)
        if [ -n "$unresolved" ]; then
            echo "ERROR: $f has unresolved libraries:" >&2
            echo "$unresolved" >&2
            bad=1
        fi
    done < <(find "$dir" -maxdepth 1 -type f \( -perm -u+x -o -name "*.so*" \))
    [ "$bad" -eq 0 ] || fail "unresolved shared libraries in $dir (missing package dependency?)"
    echo "  ✓ all shared libraries resolve in $dir"
}

verify_ide_integrations() {
    echo "Verifying IDE desktop integrations..."
    for f in \
        /usr/share/applications/antigravity-ide-url-handler.desktop \
        /usr/share/nautilus-python/extensions/open-in-antigravity-ide.py \
        /usr/share/caja-python/extensions/open-in-antigravity-ide.py \
        /usr/share/kio/servicemenus/open-in-antigravity-ide.desktop \
        /usr/share/nemo/actions/open-in-antigravity-ide.nemo_action; do
        test -e "$f" || fail "$f not installed"
        echo "  ✓ $f installed"
    done
}

verify_launch() {
    # Informational: report whether the CLI starts headless; does not gate the release
    if timeout 60 "$1" --version > /tmp/launch.out 2>&1; then
        echo "  ✓ $1 --version: $(head -n 1 /tmp/launch.out)"
    else
        echo "  ! $1 --version did not succeed headless (informational):" >&2
        head -n 5 /tmp/launch.out >&2 || true
    fi
}

if [ "${EXPECT_HUB:-0}" = 1 ]; then
    verify_app antigravity /usr/bin/antigravity /usr/bin/agy-hub antigravity.desktop
fi
if [ "${EXPECT_IDE:-0}" = 1 ]; then
    verify_app antigravity-ide /usr/bin/antigravity-ide /usr/bin/agy-ide antigravity-ide.desktop
    verify_ide_integrations
    verify_launch /usr/bin/antigravity-ide
fi
VERIFY_EOF

EXPECT_IDE=0
EXPECT_HUB=0

# 1. Fedora / RPM Installation Test
if has_pkg "*${RPM_ARCH}.rpm"; then
    EXPECT_IDE=0; EXPECT_HUB=0
    has_pkg "antigravity-ide-[0-9]*.${RPM_ARCH}.rpm" && EXPECT_IDE=1
    has_pkg "antigravity-[0-9]*.${RPM_ARCH}.rpm" && EXPECT_HUB=1

    echo -e "\n---> [1/2] Testing RPM installation in Fedora container (${PLATFORM})..."
    RPM_SCRIPT='
        set -euo pipefail
        echo "Installing packages with DNF..."
        dnf install -y /packages/*'"${RPM_ARCH}"'.rpm glibc-common

        echo "Verifying package database..."
        [ "$EXPECT_HUB" = 1 ] && rpm -q antigravity
        [ "$EXPECT_IDE" = 1 ] && rpm -q antigravity-ide

        echo "Verifying installed file ownership..."
        bad_owner=$(rpm -qa --qf "[%{FILEUSERNAME}\n]" antigravity antigravity-ide 2>/dev/null | grep -v "^root$" | head -n 1 || true)
        [ -z "$bad_owner" ] || { echo "ERROR: package has files not owned by root (found owner $bad_owner)" >&2; exit 1; }

        '
    # shellcheck disable=SC2016
    "${ENGINE}" run --rm --platform "${PLATFORM}" \
        -e "EXPECT_IDE=${EXPECT_IDE}" -e "EXPECT_HUB=${EXPECT_HUB}" \
        -v "${PKG_DIR_ABS}:/packages:ro${SELINUX_FLAG}" \
        docker.io/library/fedora:latest bash -c "${RPM_SCRIPT}
        ${VERIFY_COMMON}
        echo \"RPM installation smoke test PASSED!\"
        "
fi

# 2. Ubuntu / DEB Installation Test
if has_pkg "*_${DEB_ARCH}.deb"; then
    EXPECT_IDE=0; EXPECT_HUB=0
    has_pkg "antigravity-ide_[0-9]*_${DEB_ARCH}.deb" && EXPECT_IDE=1
    has_pkg "antigravity_[0-9]*_${DEB_ARCH}.deb" && EXPECT_HUB=1

    echo -e "\n---> [2/2] Testing DEB installation in Ubuntu container (${PLATFORM})..."
    DEB_SCRIPT='
        set -euo pipefail
        echo "Updating apt indexes..."
        apt-get update -qq

        echo "Installing packages with APT..."
        DEBIAN_FRONTEND=noninteractive apt-get install -y /packages/*_'"${DEB_ARCH}"'.deb

        echo "Verifying package database..."
        [ "$EXPECT_HUB" = 1 ] && dpkg -s antigravity > /dev/null
        [ "$EXPECT_IDE" = 1 ] && dpkg -s antigravity-ide > /dev/null

        echo "Verifying package file integrity (md5sums)..."
        if command -v dpkg > /dev/null && dpkg --verify antigravity antigravity-ide 2>/dev/null | grep -q .; then
            dpkg --verify antigravity antigravity-ide >&2 || true
            echo "ERROR: dpkg --verify reported modified files" >&2
            exit 1
        fi

        '
    # shellcheck disable=SC2016
    "${ENGINE}" run --rm --platform "${PLATFORM}" \
        -e "EXPECT_IDE=${EXPECT_IDE}" -e "EXPECT_HUB=${EXPECT_HUB}" \
        -v "${PKG_DIR_ABS}:/packages:ro${SELINUX_FLAG}" \
        docker.io/library/ubuntu:24.04 bash -c "${DEB_SCRIPT}
        ${VERIFY_COMMON}
        echo \"DEB installation smoke test PASSED!\"
        "
fi

echo -e "\n=== All Package Smoke Tests Completed Successfully! ==="
