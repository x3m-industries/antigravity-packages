#!/usr/bin/env python3
"""
Injects dynamic release versions and tooltips into dist/index.html based on the GitHub release tag.
Release tag format: v{ide_version}_hub-{hub_version}
Example: v2.5.5-4923483625488384_hub-2.19.1-6046815158665216
"""
import sys
import re
from pathlib import Path


def parse_release_tag(tag: str):
    """
    Parses a combined or single release tag into IDE and Hub version components.
    Returns: (ide_semver, ide_build, hub_semver, hub_build) or None
    """
    if not tag or tag in ["latest", "vlatest"]:
        return None
    # Combined tag: v<ide_ver>-<ide_build>_hub-<hub_ver>-<hub_build>
    m = re.match(r"^v([0-9\.]+)(?:-([0-9a-zA-Z\.\-]+))?_hub-([0-9\.]+)(?:-([0-9a-zA-Z\.\-]+))?", tag)
    if m:
        return m.groups()

    # Single tag fallback: v<ver>-<build>
    m_simple = re.match(r"^v([0-9\.]+)(?:-([0-9a-zA-Z\.\-]+))?", tag)
    if m_simple:
        ver, b = m_simple.groups()
        return ver, b, ver, b

    return None


def _replace_title_on_data_version_full(html_content: str, app_key: str, full_version: str) -> str:
    """Replaces title="..." on any HTML opening tag that has data-version-full="<app_key>", regardless of attribute order."""
    pattern = re.compile(rf'<[^>]+data-version-full=["\']{re.escape(app_key)}["\'][^>]*>')

    def _repl(match):
        tag_str = match.group(0)
        return re.sub(
            r'title=(["\'])[^"\']*\1',
            f'title="Latest packaged release: {full_version}"',
            tag_str,
        )

    return pattern.sub(_repl, html_content)


def inject_versions_into_html(html_content: str, tag: str) -> str:
    """
    Replaces data-version spans, data-version-full titles, .deb artifact filenames,
    and JSON-LD softwareVersion fields in HTML with release tag values.
    """
    parsed = parse_release_tag(tag)
    if not parsed:
        return html_content

    ide_ver, ide_b, hub_ver, hub_b = parsed

    # Replace IDE semver spans
    html_content = re.sub(
        r'(<[^>]+data-version=["\']ide-semver["\'][^>]*>)[^<]*(</[^>]+>)',
        rf'\g<1>v{ide_ver}\g<2>',
        html_content
    )
    # Replace Hub semver spans
    html_content = re.sub(
        r'(<[^>]+data-version=["\']hub-semver["\'][^>]*>)[^<]*(</[^>]+>)',
        rf'\g<1>v{hub_ver}\g<2>',
        html_content
    )
    # Update IDE full build titles (order-independent) and .deb filenames
    if ide_b:
        html_content = _replace_title_on_data_version_full(html_content, "ide", f"{ide_ver}-{ide_b}")
        html_content = re.sub(
            r'antigravity-ide_(?:[0-9]+\.[0-9]+\.[0-9]+-[0-9a-zA-Z\.\-]+|latest)_(amd64|arm64)\.deb',
            rf'antigravity-ide_{ide_ver}-{ide_b}_\1.deb',
            html_content
        )
    # Update Hub full build titles (order-independent) and .deb filenames
    if hub_b:
        html_content = _replace_title_on_data_version_full(html_content, "hub", f"{hub_ver}-{hub_b}")
        html_content = re.sub(
            r'(?<![a-zA-Z0-9_-])antigravity_(?:[0-9]+\.[0-9]+\.[0-9]+-[0-9a-zA-Z\.\-]+|latest)_(amd64|arm64)\.deb',
            rf'antigravity_{hub_ver}-{hub_b}_\1.deb',
            html_content
        )

    # Update JSON-LD softwareVersion for combined and individual entries
    html_content = re.sub(
        r'("softwareVersion"\s*:\s*")[^"]*\(IDE\)\s*/\s*[^"]*\(Hub\)(")',
        rf'\g<1>{ide_ver} (IDE) / {hub_ver} (Hub)\g<2>',
        html_content
    )
    html_content = re.sub(
        r'("name"\s*:\s*"Google Antigravity IDE \(antigravity-ide\)"[^}]*?"softwareVersion"\s*:\s*")[^"]*(")',
        rf'\g<1>{ide_ver}\g<2>',
        html_content
    )
    html_content = re.sub(
        r'("name"\s*:\s*"Google Antigravity Agent Hub \(antigravity\)"[^}]*?"softwareVersion"\s*:\s*")[^"]*(")',
        rf'\g<1>{hub_ver}\g<2>',
        html_content
    )

    return html_content


def main():
    if len(sys.argv) < 3:
        print("Usage: inject_versions.py <release_tag> <path_to_html_file>", file=sys.stderr)
        sys.exit(1)

    tag = sys.argv[1]
    html_path = Path(sys.argv[2])

    if not html_path.exists():
        print(f"Error: {html_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    parsed = parse_release_tag(tag)
    if not parsed:
        print(f"Skipping version injection: tag '{tag}' is not a versioned tag.")
        sys.exit(0)

    ide_ver, _, hub_ver, _ = parsed
    content = html_path.read_text(encoding="utf-8")
    updated_content = inject_versions_into_html(content, tag)
    html_path.write_text(updated_content, encoding="utf-8")
    print(f"Injected release versions into {html_path.name}: IDE v{ide_ver}, Hub v{hub_ver}")


if __name__ == "__main__":
    main()
