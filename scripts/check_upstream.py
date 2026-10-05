#!/usr/bin/env python3
import urllib.request
import fnmatch
import gzip
import re
import json
import sys
import os
import subprocess

RPM_ARCHES = ("x86_64", "aarch64")
DEB_ARCHES = ("amd64", "arm64")
TRUTHY = ("true", "1", "yes")


class UpstreamError(Exception):
    """Raised when the upstream download page does not contain everything we need."""


def get_latest_upstream():
    url = "https://antigravity.google/download"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip",
        }
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        try:
            html = gzip.decompress(raw).decode("utf-8", errors="ignore")
        except Exception:
            html = raw.decode("utf-8", errors="ignore")

    # Antigravity Hub
    hub_match = re.search(r'https://storage\.googleapis\.com/antigravity-public/antigravity-hub/([0-9a-zA-Z\.\-]+)/linux-x64/Antigravity\.tar\.gz', html)
    hub_arm_match = re.search(r'https://storage\.googleapis\.com/antigravity-public/antigravity-hub/([0-9a-zA-Z\.\-]+)/linux-arm/Antigravity\.tar\.gz', html)

    # Antigravity IDE
    ide_match = re.search(r'https://edgedl\.me\.gvt1\.com/edgedl/release2/[^\"\' ]+/([0-9a-zA-Z\.\-]+)/linux-x64/Antigravity(?:%20|\+)IDE\.tar\.gz', html)
    ide_arm_match = re.search(r'https://edgedl\.me\.gvt1\.com/edgedl/release2/[^\"\' ]+/([0-9a-zA-Z\.\-]+)/linux-arm/Antigravity(?:%20|\+)IDE\.tar\.gz', html)

    return {
        "antigravity": {
            "version_full": hub_match.group(1) if hub_match else None,
            "url_x64": hub_match.group(0) if hub_match else None,
            "url_arm64": hub_arm_match.group(0) if hub_arm_match else None,
        },
        "antigravity-ide": {
            "version_full": ide_match.group(1) if ide_match else None,
            "url_x64": ide_match.group(0) if ide_match else None,
            "url_arm64": ide_arm_match.group(0) if ide_arm_match else None,
        }
    }

def get_latest_release():
    try:
        res = subprocess.run(["gh", "release", "view", "--json", "tagName,assets"], capture_output=True, text=True)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception as e:
        print(f"Warning checking GitHub releases: {e}", file=sys.stderr)
    return None


def validate_upstream(upstream):
    """Ensure every app has a version and both architecture URLs.

    A partial scrape (e.g. Google changed the page markup) must never lead to a
    release that silently drops packages from the DNF/APT repositories.
    """
    problems = []
    for pkg in ("antigravity", "antigravity-ide"):
        info = upstream.get(pkg) or {}
        for key in ("version_full", "url_x64", "url_arm64"):
            if not info.get(key):
                problems.append(f"{pkg}: missing '{key}'")
    if problems:
        raise UpstreamError(
            "Upstream download page did not contain all expected assets: " + "; ".join(problems)
        )


def asset_patterns(pkg, version_full):
    """Glob patterns for every package file expected for an app version (any packaging revision)."""
    patterns = [f"{pkg}-{version_full}*.{arch}.rpm" for arch in RPM_ARCHES]
    patterns += [f"{pkg}_{version_full}*_{arch}.deb" for arch in DEB_ARCHES]
    return patterns


def app_complete(pkg, version_full, assets):
    """True when the release already ships all rpm/deb x arch files for this version."""
    return all(
        any(fnmatch.fnmatch(a, pat) for a in assets)
        for pat in asset_patterns(pkg, version_full)
    )


def existing_version(pkg, version_full, assets):
    """Version string (including any packaging revision) of the assets already published."""
    pat = re.compile(rf"^{re.escape(pkg)}-({re.escape(version_full)}[^/]*)\.x86_64\.rpm$")
    found = sorted(m.group(1) for m in (pat.match(a) for a in assets) if m)
    return found[-1] if found else version_full


def compute_build_plan(upstream, prev_tag, existing_assets, env):
    """Decide what needs building. Pure function: no network, no filesystem."""
    validate_upstream(upstream)

    ide_ver = upstream["antigravity-ide"]["version_full"]
    hub_ver = upstream["antigravity"]["version_full"]

    ide_present = app_complete("antigravity-ide", ide_ver, existing_assets)
    hub_present = app_complete("antigravity", hub_ver, existing_assets)

    force_build = env.get("FORCE_BUILD", "").lower() in TRUTHY
    force_ide = env.get("FORCE_IDE", "").lower() in TRUTHY or force_build
    force_hub = env.get("FORCE_HUB", "").lower() in TRUTHY or force_build

    ide_needs_build = not ide_present or force_ide
    hub_needs_build = not hub_present or force_hub

    # A packaging revision re-rolls the apps that were explicitly forced; when
    # none were forced explicitly it applies to both.
    pkg_revision = env.get("PKG_REVISION", "").strip()
    ide_out, hub_out = ide_ver, hub_ver
    if pkg_revision:
        rev_ide = force_ide or not force_hub
        rev_hub = force_hub or not force_ide
        if rev_ide:
            ide_needs_build = True
            ide_out = f"{ide_ver}.{pkg_revision}"
        if rev_hub:
            hub_needs_build = True
            hub_out = f"{hub_ver}.{pkg_revision}"

    # Apps that are reused keep the exact version string they were published with
    if not ide_needs_build:
        ide_out = existing_version("antigravity-ide", ide_ver, existing_assets)
    if not hub_needs_build:
        hub_out = existing_version("antigravity", hub_ver, existing_assets)

    return {
        "has_update": ide_needs_build or hub_needs_build,
        "ide_needs_build": ide_needs_build,
        "hub_needs_build": hub_needs_build,
        "ide_present": ide_present,
        "hub_present": hub_present,
        # Target tag combines both versions so it is always unique when either updates
        "tag_name": f"v{ide_out}_hub-{hub_out}",
        "prev_tag": prev_tag,
        "ide_version": ide_out,
        "hub_version": hub_out,
        "ide_url_x64": upstream["antigravity-ide"]["url_x64"],
        "ide_url_arm64": upstream["antigravity-ide"]["url_arm64"],
        "hub_url_x64": upstream["antigravity"]["url_x64"],
        "hub_url_arm64": upstream["antigravity"]["url_arm64"],
    }


def write_github_output(plan, path):
    keys = [
        "has_update", "ide_needs_build", "hub_needs_build", "tag_name", "prev_tag",
        "ide_version", "ide_url_x64", "ide_url_arm64",
        "hub_version", "hub_url_x64", "hub_url_arm64",
    ]
    with open(path, "a") as f:
        for key in keys:
            value = plan[key]
            if isinstance(value, bool):
                value = "true" if value else "false"
            f.write(f"{key}={value or ''}\n")


def main():
    upstream = get_latest_upstream()
    print("Upstream versions:", json.dumps(upstream, indent=2))

    latest_rel = get_latest_release()
    prev_tag = latest_rel.get("tagName", "") if latest_rel else ""
    existing_assets = [a.get("name", "") for a in latest_rel.get("assets", [])] if latest_rel else []

    print(f"Latest release tag: {prev_tag}")
    print(f"Existing assets count: {len(existing_assets)}")

    try:
        plan = compute_build_plan(upstream, prev_tag, existing_assets, os.environ)
    except UpstreamError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"ide_needs_build: {plan['ide_needs_build']} (output: {plan['ide_version']}, present: {plan['ide_present']})")
    print(f"hub_needs_build: {plan['hub_needs_build']} (output: {plan['hub_version']}, present: {plan['hub_present']})")
    print(f"has_update: {plan['has_update']}, target tag: {plan['tag_name']}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        write_github_output(plan, github_output)

if __name__ == "__main__":
    main()
