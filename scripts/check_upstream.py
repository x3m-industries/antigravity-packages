#!/usr/bin/env python3
import urllib.request
import gzip
import re
import json
import sys
import os
import subprocess

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

def main():
    upstream = get_latest_upstream()
    print("Upstream versions:", json.dumps(upstream, indent=2))
    
    ide_ver = upstream["antigravity-ide"]["version_full"]
    hub_ver = upstream["antigravity"]["version_full"]

    latest_rel = get_latest_release()
    prev_tag = latest_rel.get("tagName", "") if latest_rel else ""
    existing_assets = [a.get("name", "") for a in latest_rel.get("assets", [])] if latest_rel else []

    print(f"Latest release tag: {prev_tag}")
    print(f"Existing assets count: {len(existing_assets)}")

    # Check if ide_ver is already in the latest release assets
    ide_present = any(f"antigravity-ide-{ide_ver}" in a or f"antigravity-ide_{ide_ver}" in a for a in existing_assets)
    # Check if hub_ver is already in the latest release assets
    hub_present = any(f"antigravity-{hub_ver}" in a or f"antigravity_{hub_ver}" in a for a in existing_assets)

    ide_needs_build = not ide_present
    hub_needs_build = not hub_present

    # Environment overrides
    force_build = os.environ.get("FORCE_BUILD", "").lower() in ["true", "1", "yes"]
    force_ide = os.environ.get("FORCE_IDE", "").lower() in ["true", "1", "yes"] or force_build
    force_hub = os.environ.get("FORCE_HUB", "").lower() in ["true", "1", "yes"] or force_build

    if force_ide:
        ide_needs_build = True
    if force_hub:
        hub_needs_build = True

    has_update = ide_needs_build or hub_needs_build

    # Target tag name combines both versions so it is always unique when either updates
    tag_name = f"v{ide_ver}_hub-{hub_ver}"
    if not prev_tag:
        tag_name = f"v{ide_ver}"

    print(f"ide_needs_build: {ide_needs_build} (upstream: {ide_ver}, present: {ide_present})")
    print(f"hub_needs_build: {hub_needs_build} (upstream: {hub_ver}, present: {hub_present})")
    print(f"has_update: {has_update}, target tag: {tag_name}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"has_update={'true' if has_update else 'false'}\n")
            f.write(f"ide_needs_build={'true' if ide_needs_build else 'false'}\n")
            f.write(f"hub_needs_build={'true' if hub_needs_build else 'false'}\n")
            f.write(f"tag_name={tag_name}\n")
            f.write(f"prev_tag={prev_tag}\n")
            f.write(f"ide_version={ide_ver}\n")
            f.write(f"ide_url_x64={upstream['antigravity-ide']['url_x64'] or ''}\n")
            f.write(f"ide_url_arm64={upstream['antigravity-ide']['url_arm64'] or ''}\n")
            f.write(f"hub_version={hub_ver}\n")
            f.write(f"hub_url_x64={upstream['antigravity']['url_x64'] or ''}\n")
            f.write(f"hub_url_arm64={upstream['antigravity']['url_arm64'] or ''}\n")

if __name__ == "__main__":
    main()
