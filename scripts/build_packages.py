#!/usr/bin/env python3
"""
Package builder for Antigravity & Antigravity IDE.
Builds both .rpm and .deb packages from Google's official tarballs.
Supports x86_64 and aarch64 / arm64.
"""

import os
import sys
import shutil
import subprocess
import tarfile
import struct
import json
import argparse
import urllib.request
from pathlib import Path

def extract_asar_file(asar_path, target_file, output_path):
    """Extract a specific file from an Electron asar archive."""
    with open(asar_path, "rb") as f:
        buf = f.read(16)
        if len(buf) < 16:
            return False
        magic, header_size, header_json_size, header_len = struct.unpack('<IIII', buf)
        header_json = f.read(header_len).decode('utf-8', errors='ignore')
        header = json.loads(header_json)
        
        file_info = header.get("files", {}).get(target_file)
        if not file_info:
            return False
        
        offset = int(file_info["offset"])
        size = int(file_info["size"])
        f.seek(16 + header_len + offset)
        data = f.read(size)
        with open(output_path, "wb") as out:
            out.write(data)
        return True

def download_file(url, output_path):
    print(f"Downloading {url} -> {output_path}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    )
    with urllib.request.urlopen(req) as resp, open(output_path, "wb") as out:
        shutil.copyfileobj(resp, out)
    print("Download complete.")

def split_version(version_full):
    """Split 2.5.5-4923483625488384 into version and release."""
    if "-" in version_full:
        parts = version_full.split("-", 1)
        return parts[0], parts[1]
    return version_full, "1"

def build_rpm(package_name, version, release, arch, app_source_dir, output_dir, desktop_file, icon_file):
    rpm_arch = "aarch64" if arch in ["aarch64", "arm64", "arm"] else "x86_64"
    print(f"\n--- Building RPM: {package_name}-{version}-{release}.{rpm_arch}.rpm ---")
    work_dir = Path(f"/tmp/rpmbuild-work-{package_name}-{rpm_arch}")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    
    rpm_root = work_dir / "rpmbuild"
    for sub in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
        (rpm_root / sub).mkdir(parents=True, exist_ok=True)

    install_dest = f"/usr/share/{package_name}"
    bin_target = f"{install_dest}/bin/{package_name}" if package_name == "antigravity-ide" else f"{install_dest}/{package_name}"

    icon_install = ""
    icon_files = ""
    if os.path.exists(icon_file):
        icon_install = f"""
mkdir -p %{{buildroot}}/usr/share/icons/hicolor/512x512/apps
mkdir -p %{{buildroot}}/usr/share/pixmaps
cp "{icon_file}" %{{buildroot}}/usr/share/icons/hicolor/512x512/apps/{package_name}.png
cp "{icon_file}" %{{buildroot}}/usr/share/pixmaps/{package_name}.png
"""
        icon_files = f"""
/usr/share/icons/hicolor/512x512/apps/{package_name}.png
/usr/share/pixmaps/{package_name}.png
"""

    spec_content = f"""
%define _topdir {rpm_root}
%define _rpmdir {output_dir}
%define __strip /bin/true
%define _missing_doc_files_terminate_build 0
%define _build_id_links none

Name:           {package_name}
Version:        {version}
Release:        {release}%{{?dist}}
Summary:        Google Antigravity - {"Agentic IDE" if "ide" in package_name else "Agent Platform"}
License:        Proprietary
URL:            https://antigravity.google
AutoReqProv:    no

Requires:       gtk3, libnotify, nss, alsa-lib, libXScrnSaver

%description
Google Antigravity packages distributed for Linux.

%install
mkdir -p "%{{buildroot}}{install_dest}"
cp -r "{app_source_dir}"/* "%{{buildroot}}{install_dest}/"

# Permissions
find "%{{buildroot}}{install_dest}" -type f -exec chmod 0644 {{}} +
find "%{{buildroot}}{install_dest}" -type d -exec chmod 0755 {{}} +
chmod 0755 "%{{buildroot}}{install_dest}/{package_name}" 2>/dev/null || true
chmod 0755 "%{{buildroot}}{install_dest}/bin/{package_name}" 2>/dev/null || true
chmod 0755 "%{{buildroot}}{install_dest}/chrome-sandbox" 2>/dev/null || true

# Symlink to /usr/bin
mkdir -p "%{{buildroot}}/usr/bin"
ln -sf "{bin_target}" "%{{buildroot}}/usr/bin/{package_name}"

# Desktop entry
mkdir -p "%{{buildroot}}/usr/share/applications"
cp "{desktop_file}" "%{{buildroot}}/usr/share/applications/{package_name}.desktop"
{icon_install}

%files
{install_dest}
/usr/bin/{package_name}
/usr/share/applications/{package_name}.desktop
{icon_files}

%post
update-desktop-database /usr/share/applications &> /dev/null || true
gtk-update-icon-cache -f /usr/share/icons/hicolor &> /dev/null || true

%postun
update-desktop-database /usr/share/applications &> /dev/null || true
gtk-update-icon-cache -f /usr/share/icons/hicolor &> /dev/null || true
"""

    spec_file = rpm_root / "SPECS" / f"{package_name}.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)

    subprocess.run(["rpmbuild", "-bb", "--target", rpm_arch, str(spec_file)], check=True)
    print("RPM build successful.")

def build_deb(package_name, version, release, arch, app_source_dir, output_dir, desktop_file, icon_file):
    deb_arch = "arm64" if arch in ["aarch64", "arm64", "arm"] else "amd64"
    deb_version = f"{version}-{release}"
    print(f"\n--- Building DEB: {package_name}_{deb_version}_{deb_arch}.deb ---")

    stage_dir = Path(f"/tmp/debbuild-work-{package_name}-{deb_arch}") / f"{package_name}_{deb_version}_{deb_arch}"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)

    install_dest = stage_dir / "usr" / "share" / package_name
    install_dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_source_dir, install_dest, dirs_exist_ok=True)

    # Permissions
    for root, dirs, files in os.walk(install_dest):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            p = os.path.join(root, f)
            if f in [package_name, "chrome-sandbox", "chrome_crashpad_handler"] or "/bin/" in p:
                os.chmod(p, 0o755)
            else:
                os.chmod(p, 0o644)

    # Bin symlink
    bin_dir = stage_dir / "usr" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target_link = f"/usr/share/{package_name}/bin/{package_name}" if package_name == "antigravity-ide" else f"/usr/share/{package_name}/{package_name}"
    os.symlink(target_link, bin_dir / package_name)

    # Desktop file
    apps_dir = stage_dir / "usr" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(desktop_file, apps_dir / f"{package_name}.desktop")

    # Icon
    if os.path.exists(icon_file):
        icon_dir = stage_dir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps"
        pix_dir = stage_dir / "usr" / "share" / "pixmaps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        pix_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(icon_file, icon_dir / f"{package_name}.png")
        shutil.copy(icon_file, pix_dir / f"{package_name}.png")

    # DEBIAN control
    debian_dir = stage_dir / "DEBIAN"
    debian_dir.mkdir(parents=True, exist_ok=True)
    
    control_content = f"""Package: {package_name}
Version: {deb_version}
Section: devel
Priority: optional
Architecture: {deb_arch}
Depends: libgtk-3-0, libnotify4, libnss3, libxss1, libasound2
Maintainer: X3M Antigravity Packagers <packaging@x3m.industries>
Description: Google Antigravity - {"Agentic IDE" if "ide" in package_name else "Agent Platform"}
 Google Antigravity packages for Debian and Ubuntu based distributions.
"""
    with open(debian_dir / "control", "w") as f:
        f.write(control_content)

    postinst_content = """#!/bin/sh
set -e
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor || true
fi
"""
    with open(debian_dir / "postinst", "w") as f:
        f.write(postinst_content)
    os.chmod(debian_dir / "postinst", 0o755)

    postrm_content = """#!/bin/sh
set -e
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor || true
fi
"""
    with open(debian_dir / "postrm", "w") as f:
        f.write(postrm_content)
    os.chmod(debian_dir / "postrm", 0o755)

    output_deb = Path(output_dir) / f"{package_name}_{deb_version}_{deb_arch}.deb"
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(stage_dir), str(output_deb)], check=True)
    print(f"DEB build successful: {output_deb}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, choices=["antigravity", "antigravity-ide"])
    parser.add_argument("--version-full", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--arch", default="x86_64")
    parser.add_argument("--output-dir", default="./dist/packages")
    parser.add_argument("--tarball", help="Optional local tarball path instead of downloading")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    version, release = split_version(args.version_full)
    work_dir = Path(f"/tmp/pkg-work-{args.package}-{args.arch}")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    tar_path = args.tarball
    if not tar_path or not os.path.exists(tar_path):
        tar_path = str(work_dir / "download.tar.gz")
        download_file(args.url, tar_path)

    print(f"Extracting {tar_path}...")
    with tarfile.open(tar_path, "r:gz") as t:
        t.extractall(work_dir)

    # Identify unpacked directory and rename it to a clean path with no spaces
    dirs = [d for d in work_dir.iterdir() if d.is_dir() and d.name != "app_source"]
    raw_dir = dirs[0]
    app_dir = work_dir / "app_source"
    raw_dir.rename(app_dir)
    print(f"App directory sanitized: {app_dir}")

    # Desktop & icon setup
    repo_root = Path(__file__).resolve().parent.parent
    desktop_file = repo_root / "desktop" / f"{args.package}.desktop"
    icon_file = work_dir / f"{args.package}.png"

    if args.package == "antigravity-ide":
        ide_icon = app_dir / "resources" / "app" / "resources" / "linux" / "code.png"
        if ide_icon.exists():
            shutil.copy(ide_icon, icon_file)
    else:
        asar_path = app_dir / "resources" / "app.asar"
        if asar_path.exists():
            extract_asar_file(str(asar_path), "icon.png", str(icon_file))

    # Build RPM
    build_rpm(args.package, version, release, args.arch, str(app_dir), str(out_dir), str(desktop_file), str(icon_file))

    # Build DEB if dpkg-deb available
    if shutil.which("dpkg-deb"):
        build_deb(args.package, version, release, args.arch, str(app_dir), str(out_dir), str(desktop_file), str(icon_file))
    else:
        print("Note: dpkg-deb not found on this system, skipping local DEB build.")

if __name__ == "__main__":
    main()
