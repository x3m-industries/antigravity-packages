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

def get_existing_releases():
    try:
        res = subprocess.run(["gh", "release", "list", "--json", "tagName"], capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return [r["tagName"] for r in data]
    except Exception as e:
        print(f"Warning checking GitHub releases: {e}", file=sys.stderr)
    return []

def main():
    upstream = get_latest_upstream()
    print("Upstream versions:", json.dumps(upstream, indent=2))
    
    existing = get_existing_releases()
    print("Existing GitHub releases:", existing)

    ide_ver = upstream["antigravity-ide"]["version_full"]
    hub_ver = upstream["antigravity"]["version_full"]

    # Target tag name combines both versions or primary IDE version
    tag_name = f"v{ide_ver}"
    has_update = tag_name not in existing

    # Check if forced via env
    if os.environ.get("FORCE_BUILD", "").lower() in ["true", "1", "yes"]:
        has_update = True
        print("Build forced via FORCE_BUILD")

    print(f"Tag: {tag_name}, has_update: {has_update}")

    # Set GitHub Actions output if in GITHUB_OUTPUT environment
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"has_update={'true' if has_update else 'false'}\n")
            f.write(f"tag_name={tag_name}\n")
            f.write(f"ide_version={ide_ver}\n")
            f.write(f"ide_url_x64={upstream['antigravity-ide']['url_x64'] or ''}\n")
            f.write(f"ide_url_arm64={upstream['antigravity-ide']['url_arm64'] or ''}\n")
            f.write(f"hub_version={hub_ver}\n")
            f.write(f"hub_url_x64={upstream['antigravity']['url_x64'] or ''}\n")
            f.write(f"hub_url_arm64={upstream['antigravity']['url_arm64'] or ''}\n")

if __name__ == "__main__":
    main()
