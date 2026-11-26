#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Post-Deploy Live Repository Verification
# Verifies live https://rpm.x3m.industries/rpm/ (zypper + dnf) and
# https://apt.x3m.industries/deb/ (apt) endpoints, GPG signatures, and 307
# redirects to GitHub Releases end-to-end.
# ==============================================================================

RPM_BASE="${RPM_BASE:-https://rpm.x3m.industries/rpm}"
APT_BASE="${APT_BASE:-https://apt.x3m.industries/deb}"

echo "=== Verifying Live RPM & APT Repositories ==="
echo "RPM endpoint: ${RPM_BASE}/"
echo "APT endpoint: ${APT_BASE}/"

# 1. Verify live HTTP metadata and gzip repodata format (with brief CDN propagation retry)
echo -e "\n---> [1/4] Checking live HTTP endpoints & repodata compression..."
repo_cfg=$(curl -fsSL -H "Cache-Control: no-cache" "${RPM_BASE}/antigravity.repo")
echo "${repo_cfg}" | grep -q "baseurl=${RPM_BASE}/" || {
    echo "ERROR: ${RPM_BASE}/antigravity.repo does not point to ${RPM_BASE}/" >&2
    exit 1
}
echo "  ✓ antigravity.repo points to ${RPM_BASE}/"

repomd_ok=false
for attempt in 1 2 3 4 5 6; do
    repomd=$(curl -fsSL -H "Cache-Control: no-cache" "${RPM_BASE}/repodata/repomd.xml")
    if echo "${repomd}" | grep -q 'primary\.xml\.gz"'; then
        repomd_ok=true
        break
    fi
    echo "  Waiting for CDN to serve gzip repomd.xml (attempt ${attempt}/6)..."
    sleep 10
done
if [ "${repomd_ok}" != "true" ]; then
    echo "ERROR: repomd.xml does not reference gzip-compressed primary.xml.gz" >&2
    exit 1
fi
echo "  ✓ repodata uses universally compatible gzip compression (primary.xml.gz)"

curl -fsSI "${RPM_BASE}/repodata/repomd.xml.asc" > /dev/null
curl -fsSI "${RPM_BASE}/RPM-GPG-KEY-antigravity" > /dev/null
curl -fsSI "${APT_BASE}/dists/stable/InRelease" > /dev/null
curl -fsSI "${APT_BASE}/antigravity.gpg" > /dev/null
echo "  ✓ signed RPM and APT metadata & public keys reachable"

ENGINE=""
if command -v docker > /dev/null 2>&1; then
    ENGINE="docker"
elif command -v podman > /dev/null 2>&1; then
    ENGINE="podman"
fi

if [ -z "${ENGINE}" ]; then
    echo "No container engine available (docker/podman). Skipping live container repo checks."
    exit 0
fi

# 2. openSUSE Tumbleweed (zypper + rpm 4.x) end-to-end download & signature check
echo -e "\n---> [2/4] Testing live zypper download & rpm 4.x signatures in openSUSE Tumbleweed..."
# shellcheck disable=SC2016
SUSE_LIVE_SCRIPT='
    set -euo pipefail
    rm -f /etc/zypp/repos.d/*.repo
    rpm --version
    rpm --import "'"${RPM_BASE}"'/RPM-GPG-KEY-antigravity"
    zypper --non-interactive addrepo -f "'"${RPM_BASE}"'/" antigravity
    zypper --non-interactive refresh antigravity
    zypper --non-interactive info antigravity antigravity-ide
    zypper --non-interactive download antigravity antigravity-ide
    shopt -s globstar nullglob
    found=0
    for pkg in /var/cache/zypp/packages/antigravity/**/*.rpm; do
        [ -f "$pkg" ] || continue
        found=$((found + 1))
        echo "Verifying downloaded RPM signature: $(basename "$pkg")"
        out=$(rpm -Kv "$pkg")
        echo "$out"
        echo "$out" | grep -qiE "Header .*Signature.*: OK" || {
            echo "ERROR: rpm 4.x did not verify signature on $pkg" >&2
            exit 1
        }
    done
    [ "$found" -ge 2 ] || { echo "ERROR: expected at least 2 downloaded RPMs, found $found" >&2; exit 1; }
    echo "Live openSUSE zypper check PASSED!"
'
"${ENGINE}" run --rm docker.io/opensuse/tumbleweed:latest bash -c "${SUSE_LIVE_SCRIPT}"

# 3. Fedora (dnf) live metadata & GPG key verification
echo -e "\n---> [3/4] Testing live DNF repository in Fedora..."
DNF_LIVE_SCRIPT='
    set -euo pipefail
    curl -fsSL "'"${RPM_BASE}"'/antigravity.repo" -o /etc/yum.repos.d/antigravity.repo
    dnf --disablerepo="*" --enablerepo=antigravity -y makecache
    dnf --disablerepo="*" --enablerepo=antigravity info antigravity antigravity-ide
    echo "Live Fedora DNF check PASSED!"
'
"${ENGINE}" run --rm docker.io/library/fedora:latest bash -c "${DNF_LIVE_SCRIPT}"

# 4. Ubuntu (apt) live metadata, GPG verification, and 307 redirect download
echo -e "\n---> [4/4] Testing live APT repository & redirect download in Ubuntu..."
# shellcheck disable=SC2016
APT_LIVE_SCRIPT='
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt_ok=false
    for attempt in 1 2 3; do
        if apt-get update -qq -o Acquire::Retries=3 && \
           apt-get install -y -qq --no-install-recommends -o Acquire::Retries=3 curl ca-certificates; then
            apt_ok=true
            break
        fi
        echo "APT bootstrap failed (attempt ${attempt}/3); clearing apt lists and retrying..." >&2
        rm -rf /var/lib/apt/lists/*
        sleep $((attempt * 10))
    done
    [ "$apt_ok" = "true" ] || { echo "ERROR: apt-get bootstrap failed after 3 attempts" >&2; exit 1; }
    rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*
    mkdir -p /etc/apt/keyrings
    curl -fsSL "'"${APT_BASE}"'/antigravity.gpg" -o /etc/apt/keyrings/antigravity.gpg
    curl -fsSL "'"${APT_BASE}"'/antigravity.sources" -o /etc/apt/sources.list.d/antigravity.sources
    apt-get update
    apt-cache show antigravity antigravity-ide > /dev/null
    mkdir -p /tmp/deb-dl && chmod 0777 /tmp/deb-dl && cd /tmp/deb-dl
    apt-get download antigravity
    ls -lh /tmp/deb-dl/antigravity_*.deb
    echo "Live Ubuntu APT check PASSED!"
'
"${ENGINE}" run --rm docker.io/library/ubuntu:24.04 bash -c "${APT_LIVE_SCRIPT}"

echo -e "\n=== All Live Repository Verifications PASSED! ==="
