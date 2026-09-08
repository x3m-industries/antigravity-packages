#!/usr/bin/env python3
"""
CLI statistics tool to inspect package download metrics for Google Antigravity & Antigravity IDE.
Fetches download counts directly from the GitHub Releases API.
"""

import os
import sys
import json
import urllib.request
import argparse

REPO = "x3m-industries/antigravity-packages"

def fetch_releases():
    url = f"https://api.github.com/repos/{REPO}/releases"
    headers = {
        "User-Agent": "Antigravity-Stats/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error fetching releases from GitHub API: {e.code} {e.reason}", file=sys.stderr)
        if e.code == 403:
            print("Tip: If rate limited, export GH_TOKEN=<your_github_token>.", file=sys.stderr)
        sys.exit(1)

def analyze_downloads(releases):
    total_downloads = 0
    by_package = {"antigravity-ide": 0, "antigravity": 0}
    by_arch = {"x86_64": 0, "aarch64": 0}
    by_format = {"rpm": 0, "deb": 0}
    assets_table = []

    for rel in releases:
        tag = rel.get("tag_name", "unknown")
        for asset in rel.get("assets", []):
            name = asset.get("name", "")
            count = asset.get("download_count", 0)
            size_mb = asset.get("size", 0) / (1024 * 1024)
            total_downloads += count

            # Format
            fmt = "rpm" if name.endswith(".rpm") else "deb" if name.endswith(".deb") else "other"
            if fmt in by_format:
                by_format[fmt] += count

            # Package
            pkg = "antigravity-ide" if "antigravity-ide" in name else "antigravity" if "antigravity" in name else "other"
            if pkg in by_package:
                by_package[pkg] += count

            # Arch
            arch = "aarch64" if ("aarch64" in name or "arm64" in name) else "x86_64" if ("x86_64" in name or "amd64" in name) else "other"
            if arch in by_arch:
                by_arch[arch] += count

            assets_table.append({
                "tag": tag,
                "name": name,
                "package": pkg,
                "arch": arch,
                "format": fmt.upper(),
                "size_mb": round(size_mb, 1),
                "downloads": count
            })

    return {
        "total_downloads": total_downloads,
        "by_package": by_package,
        "by_arch": by_arch,
        "by_format": by_format,
        "assets": assets_table
    }

def print_dashboard(data):
    print("=" * 68)
    print("       🚀  GOOGLE ANTIGRAVITY LINUX PACKAGES — DOWNLOAD STATS       ")
    print("=" * 68)
    print(f"\n📦 TOTAL DOWNLOADS: {data['total_downloads']:,}\n")

    print("📊 Breakdown by Package:")
    for pkg, count in data["by_package"].items():
        pct = (count / data["total_downloads"] * 100) if data["total_downloads"] > 0 else 0
        print(f"   • {pkg:<18} : {count:>6,} ({pct:>5.1f}%)")

    print("\n🖥️  Breakdown by Architecture:")
    for arch, count in data["by_arch"].items():
        pct = (count / data["total_downloads"] * 100) if data["total_downloads"] > 0 else 0
        print(f"   • {arch:<18} : {count:>6,} ({pct:>5.1f}%)")

    print("\n📦 Breakdown by Format:")
    for fmt, count in data["by_format"].items():
        pct = (count / data["total_downloads"] * 100) if data["total_downloads"] > 0 else 0
        print(f"   • {fmt.upper():<18} : {count:>6,} ({pct:>5.1f}%)")

    print("\n" + "-" * 68)
    print(f"{'RELEASE':<14} {'PACKAGE ASSET':<38} {'SIZE':>7} {'DOWNLOADS':>9}")
    print("-" * 68)
    for a in data["assets"]:
        print(f"{a['tag']:<14} {a['name']:<38} {a['size_mb']:>5.1f}MB {a['downloads']:>9,}")
    print("-" * 68 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Package download stats for Antigravity Linux packages")
    parser.add_argument("--json", action="store_true", help="Output raw JSON data")
    args = parser.parse_args()

    releases = fetch_releases()
    data = analyze_downloads(releases)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_dashboard(data)

if __name__ == "__main__":
    main()
