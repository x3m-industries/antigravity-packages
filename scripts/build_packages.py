#!/usr/bin/env python3
"""
Package builder for Antigravity & Antigravity IDE.
Builds both .rpm and .deb packages from Google's official tarballs.
Supports x86_64 and aarch64 / arm64.
"""

import os
import sys
import hashlib
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
    try:
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
            payload_start = 8 + header_size
            f.seek(payload_start + offset)
            data = f.read(size)
            if len(data) != size:
                return False
            with open(output_path, "wb") as out:
                out.write(data)
            return True
    except Exception as e:
        print(f"Warning extracting {target_file} from {asar_path}: {e}")
        return False

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

def sanitize_tree_permissions(directory):
    """Ensure correct executable and file permissions for packaged tree.
    Directories -> 0755
    Executables (ELF binaries, scripts with shebang, binaries in bin/) -> 0755
    Regular files -> 0644
    """
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            p = os.path.join(root, f)
            if os.path.islink(p):
                continue
            is_exec = False
            if f in ["antigravity", "antigravity-ide", "chrome-sandbox", "chrome_crashpad_handler", "language_server", "webm_encoder", "rg"] or f.startswith("language_server"):
                is_exec = True
            elif f.endswith(".sh") or "/bin/" in p or "/node_modules/.bin/" in p:
                is_exec = True
            else:
                try:
                    with open(p, "rb") as fp:
                        header = fp.read(4)
                        if header == b"\x7fELF" or header[:2] == b"#!":
                            is_exec = True
                except Exception:
                    pass
            
            os.chmod(p, 0o755 if is_exec else 0o644)

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

    extra_install = ""
    extra_files = ""
    repo_root = Path(__file__).resolve().parent.parent
    desktop_dir = repo_root / "desktop"
    nautilus_src = desktop_dir / "nautilus" / "open-in-antigravity-ide.py"
    dolphin_src = desktop_dir / "dolphin" / "open-in-antigravity-ide.desktop"
    nemo_src = desktop_dir / "nemo" / "open-in-antigravity-ide.nemo_action"
    url_handler_src = desktop_dir / "antigravity-ide-url-handler.desktop"

    short_bin = "agy-ide" if package_name == "antigravity-ide" else "agy-hub"

    if package_name == "antigravity-ide":
        if url_handler_src.exists():
            extra_install += f"""
cp "{url_handler_src}" "%{{buildroot}}/usr/share/applications/antigravity-ide-url-handler.desktop"
"""
            extra_files += "/usr/share/applications/antigravity-ide-url-handler.desktop\n"

        if nautilus_src.exists():
            extra_install += f"""
mkdir -p %{{buildroot}}/usr/share/nautilus-python/extensions
cp "{nautilus_src}" %{{buildroot}}/usr/share/nautilus-python/extensions/open-in-antigravity-ide.py
chmod 0644 %{{buildroot}}/usr/share/nautilus-python/extensions/open-in-antigravity-ide.py

mkdir -p %{{buildroot}}/usr/share/caja-python/extensions
cp "{nautilus_src}" %{{buildroot}}/usr/share/caja-python/extensions/open-in-antigravity-ide.py
chmod 0644 %{{buildroot}}/usr/share/caja-python/extensions/open-in-antigravity-ide.py
"""
            extra_files += """%dir /usr/share/nautilus-python
%dir /usr/share/nautilus-python/extensions
%dir /usr/share/caja-python
%dir /usr/share/caja-python/extensions
/usr/share/nautilus-python/extensions/open-in-antigravity-ide.py
/usr/share/caja-python/extensions/open-in-antigravity-ide.py
"""

        if dolphin_src.exists():
            extra_install += f"""
mkdir -p %{{buildroot}}/usr/share/kio/servicemenus
mkdir -p %{{buildroot}}/usr/share/kservices5/ServiceMenus
cp "{dolphin_src}" %{{buildroot}}/usr/share/kio/servicemenus/open-in-antigravity-ide.desktop
chmod 0644 %{{buildroot}}/usr/share/kio/servicemenus/open-in-antigravity-ide.desktop
ln -sf /usr/share/kio/servicemenus/open-in-antigravity-ide.desktop %{{buildroot}}/usr/share/kservices5/ServiceMenus/open-in-antigravity-ide.desktop
"""
            extra_files += """%dir /usr/share/kio
%dir /usr/share/kio/servicemenus
%dir /usr/share/kservices5
%dir /usr/share/kservices5/ServiceMenus
/usr/share/kio/servicemenus/open-in-antigravity-ide.desktop
/usr/share/kservices5/ServiceMenus/open-in-antigravity-ide.desktop
"""

        if nemo_src.exists():
            extra_install += f"""
mkdir -p %{{buildroot}}/usr/share/nemo/actions
cp "{nemo_src}" %{{buildroot}}/usr/share/nemo/actions/open-in-antigravity-ide.nemo_action
chmod 0644 %{{buildroot}}/usr/share/nemo/actions/open-in-antigravity-ide.nemo_action
"""
            extra_files += """%dir /usr/share/nemo
%dir /usr/share/nemo/actions
/usr/share/nemo/actions/open-in-antigravity-ide.nemo_action
"""

        bash_comp = Path(app_source_dir) / "resources" / "completions" / "bash" / "antigravity-ide"
        if bash_comp.exists():
            extra_install += f"""
mkdir -p %{{buildroot}}/usr/share/bash-completion/completions
cp "%{{buildroot}}{install_dest}/resources/completions/bash/antigravity-ide" "%{{buildroot}}/usr/share/bash-completion/completions/antigravity-ide"
ln -sf antigravity-ide "%{{buildroot}}/usr/share/bash-completion/completions/agy-ide"
"""
            extra_files += """/usr/share/bash-completion/completions/antigravity-ide
/usr/share/bash-completion/completions/agy-ide
"""

        zsh_comp = Path(app_source_dir) / "resources" / "completions" / "zsh" / "_antigravity-ide"
        if zsh_comp.exists():
            extra_install += f"""
mkdir -p %{{buildroot}}/usr/share/zsh/site-functions
cp "%{{buildroot}}{install_dest}/resources/completions/zsh/_antigravity-ide" "%{{buildroot}}/usr/share/zsh/site-functions/_antigravity-ide"
ln -sf _antigravity-ide "%{{buildroot}}/usr/share/zsh/site-functions/_agy-ide"
"""
            extra_files += """/usr/share/zsh/site-functions/_antigravity-ide
/usr/share/zsh/site-functions/_agy-ide
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

# Soname-based dependencies resolve on both Fedora/RHEL and openSUSE (package names differ there)
Requires:       libgtk-3.so.0()(64bit), libnotify.so.4()(64bit), libnss3.so()(64bit), libasound.so.2()(64bit), libXss.so.1()(64bit), libgbm.so.1()(64bit), libxkbfile.so.1()(64bit), xdg-utils
Recommends:     libsecret-1.so.0()(64bit){"\nRecommends:     nautilus-python" if package_name == "antigravity-ide" else ""}

%description
Google Antigravity packages distributed for Linux.

%install
mkdir -p "%{{buildroot}}{install_dest}"
cp -a "{app_source_dir}"/* "%{{buildroot}}{install_dest}/"

# Modes were normalized by sanitize_tree_permissions() before packaging and are
# preserved by cp -a; ownership is forced to root:root via defattr in the files section.
chmod 0755 "%{{buildroot}}{install_dest}"
if [ -f "%{{buildroot}}{install_dest}/chrome-sandbox" ]; then
    chmod 4755 "%{{buildroot}}{install_dest}/chrome-sandbox"
fi

# Symlink to /usr/bin
mkdir -p "%{{buildroot}}/usr/bin"
ln -sf "{bin_target}" "%{{buildroot}}/usr/bin/{package_name}"
ln -sf "/usr/bin/{package_name}" "%{{buildroot}}/usr/bin/{short_bin}"

# Desktop entry
mkdir -p "%{{buildroot}}/usr/share/applications"
cp "{desktop_file}" "%{{buildroot}}/usr/share/applications/{package_name}.desktop"
{icon_install}
{extra_install}

%files
%defattr(-,root,root,-)
{install_dest}
/usr/bin/{package_name}
/usr/bin/{short_bin}
/usr/share/applications/{package_name}.desktop
{icon_files}
{extra_files}

%post
if [ -f "{install_dest}/chrome-sandbox" ]; then
    chmod 4755 "{install_dest}/chrome-sandbox" 2>/dev/null || true
fi
update-desktop-database /usr/share/applications &> /dev/null || true
gtk-update-icon-cache -f /usr/share/icons/hicolor &> /dev/null || true

%postun
update-desktop-database /usr/share/applications &> /dev/null || true
gtk-update-icon-cache -f /usr/share/icons/hicolor &> /dev/null || true
"""

    spec_file = rpm_root / "SPECS" / f"{package_name}.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)

    try:
        subprocess.run(["rpmbuild", "-bb", "--target", rpm_arch, str(spec_file)], check=True)
    finally:
        # The build tree holds a full copy of the application (~1 GB)
        shutil.rmtree(work_dir, ignore_errors=True)
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
    sanitize_tree_permissions(install_dest)
    cs_bin = install_dest / "chrome-sandbox"
    if cs_bin.exists():
        try:
            os.chmod(cs_bin, 0o4755)
        except Exception:
            pass

    # Bin symlinks
    bin_dir = stage_dir / "usr" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target_link = f"/usr/share/{package_name}/bin/{package_name}" if package_name == "antigravity-ide" else f"/usr/share/{package_name}/{package_name}"
    os.symlink(target_link, bin_dir / package_name)
    short_bin = "agy-ide" if package_name == "antigravity-ide" else "agy-hub"
    os.symlink(f"/usr/bin/{package_name}", bin_dir / short_bin)

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

    repo_root = Path(__file__).resolve().parent.parent
    desktop_dir = repo_root / "desktop"
    nautilus_src = desktop_dir / "nautilus" / "open-in-antigravity-ide.py"
    dolphin_src = desktop_dir / "dolphin" / "open-in-antigravity-ide.desktop"
    nemo_src = desktop_dir / "nemo" / "open-in-antigravity-ide.nemo_action"
    url_handler_src = desktop_dir / "antigravity-ide-url-handler.desktop"

    if package_name == "antigravity-ide":
        # URL handler desktop entry
        if url_handler_src.exists():
            shutil.copy(url_handler_src, apps_dir / "antigravity-ide-url-handler.desktop")

        # Nautilus & Caja
        if nautilus_src.exists():
            nautilus_dir = stage_dir / "usr" / "share" / "nautilus-python" / "extensions"
            nautilus_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(nautilus_src, nautilus_dir / "open-in-antigravity-ide.py")
            os.chmod(nautilus_dir / "open-in-antigravity-ide.py", 0o644)

            caja_dir = stage_dir / "usr" / "share" / "caja-python" / "extensions"
            caja_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(nautilus_src, caja_dir / "open-in-antigravity-ide.py")
            os.chmod(caja_dir / "open-in-antigravity-ide.py", 0o644)

        # KDE Dolphin Service Menu
        if dolphin_src.exists():
            kio_dir = stage_dir / "usr" / "share" / "kio" / "servicemenus"
            kio_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(dolphin_src, kio_dir / "open-in-antigravity-ide.desktop")
            os.chmod(kio_dir / "open-in-antigravity-ide.desktop", 0o644)

            kservice_dir = stage_dir / "usr" / "share" / "kservices5" / "ServiceMenus"
            kservice_dir.mkdir(parents=True, exist_ok=True)
            os.symlink("/usr/share/kio/servicemenus/open-in-antigravity-ide.desktop", kservice_dir / "open-in-antigravity-ide.desktop")

        # Nemo Action
        if nemo_src.exists():
            nemo_dir = stage_dir / "usr" / "share" / "nemo" / "actions"
            nemo_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(nemo_src, nemo_dir / "open-in-antigravity-ide.nemo_action")
            os.chmod(nemo_dir / "open-in-antigravity-ide.nemo_action", 0o644)

        # Shell completions
        bash_src = Path(app_source_dir) / "resources" / "completions" / "bash" / "antigravity-ide"
        if bash_src.exists():
            bash_dir = stage_dir / "usr" / "share" / "bash-completion" / "completions"
            bash_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(bash_src, bash_dir / "antigravity-ide")
            os.symlink("antigravity-ide", bash_dir / "agy-ide")

        zsh_src = Path(app_source_dir) / "resources" / "completions" / "zsh" / "_antigravity-ide"
        if zsh_src.exists():
            zsh_dir = stage_dir / "usr" / "share" / "zsh" / "site-functions"
            zsh_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(zsh_src, zsh_dir / "_antigravity-ide")
            os.symlink("_antigravity-ide", zsh_dir / "_agy-ide")

    # DEBIAN control
    debian_dir = stage_dir / "DEBIAN"
    debian_dir.mkdir(parents=True, exist_ok=True)

    # md5sums + Installed-Size (computed on the staged payload, excluding DEBIAN/)
    installed_bytes = 0
    md5_lines = []
    for root, dirs, files in os.walk(stage_dir):
        if Path(root) == stage_dir:
            dirs[:] = [d for d in dirs if d != "DEBIAN"]
        for name in sorted(files):
            path = Path(root) / name
            if path.is_symlink():
                continue
            installed_bytes += path.stat().st_size
            digest = hashlib.md5()
            with open(path, "rb") as fp:
                for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                    digest.update(chunk)
            md5_lines.append(f"{digest.hexdigest()}  {path.relative_to(stage_dir).as_posix()}")
    installed_size_kb = (installed_bytes + 1023) // 1024
    with open(debian_dir / "md5sums", "w") as f:
        f.write("\n".join(sorted(md5_lines, key=lambda l: l.split("  ", 1)[1])) + "\n")

    recommends_deb = "libsecret-1-0"
    if package_name == "antigravity-ide":
        recommends_deb += ", python3-nautilus"
    # libgtk-3-0 / libasound2 are provided by their t64 replacements on Ubuntu 24.04+ / Debian 13+
    control_content = f"""Package: {package_name}
Version: {deb_version}
Section: devel
Priority: optional
Architecture: {deb_arch}
Installed-Size: {installed_size_kb}
Depends: libgtk-3-0t64 | libgtk-3-0, libnotify4, libnss3, libxss1, libasound2t64 | libasound2, libgbm1, libxkbfile1, xdg-utils
Recommends: {recommends_deb}
Maintainer: X3M Antigravity Packagers <packaging@x3m.industries>
Homepage: https://github.com/x3m-industries/antigravity-packages
Description: Google Antigravity - {"Agentic IDE" if "ide" in package_name else "Agent Platform"}
 Google Antigravity packages for Debian and Ubuntu based distributions.
"""
    with open(debian_dir / "control", "w") as f:
        f.write(control_content)

    postinst_content = f"""#!/bin/sh
set -e
if [ -f "/usr/share/{package_name}/chrome-sandbox" ]; then
    chown root:root "/usr/share/{package_name}/chrome-sandbox" 2>/dev/null || true
    chmod 4755 "/usr/share/{package_name}/chrome-sandbox" 2>/dev/null || true
fi
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
    try:
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(stage_dir), str(output_deb)], check=True)
    finally:
        # The staging tree holds a full copy of the application (~1 GB)
        shutil.rmtree(stage_dir.parent, ignore_errors=True)
    print(f"DEB build successful: {output_deb}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, choices=["antigravity", "antigravity-ide"])
    parser.add_argument("--version-full", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--arch", default="x86_64")
    parser.add_argument("--output-dir", default="./dist/packages")
    parser.add_argument("--tarball", help="Optional local tarball path instead of downloading")
    parser.add_argument("--pkg-revision", help="Optional packaging release revision (e.g. 1)")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    version, release = split_version(args.version_full)
    if args.pkg_revision:
        release = f"{release}.{args.pkg_revision}"
    work_dir = Path(f"/tmp/pkg-work-{args.package}-{args.arch}")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        tar_path = args.tarball
        if not tar_path or not os.path.exists(tar_path):
            tar_path = str(work_dir / "download.tar.gz")
            download_file(args.url, tar_path)

        print(f"Extracting {tar_path}...")
        with tarfile.open(tar_path, "r:gz") as t:
            # Pin the filter so extraction semantics are identical on Python 3.12 (CI) and 3.14+
            # (whose default is the stricter "data" filter that strips special mode bits).
            if hasattr(tarfile, "tar_filter"):
                t.extractall(work_dir, filter="tar")
            else:
                t.extractall(work_dir)

        # Identify unpacked directory and rename it to a clean path with no spaces
        dirs = [d for d in work_dir.iterdir() if d.is_dir() and d.name != "app_source"]
        if len(dirs) != 1:
            raise SystemExit(
                f"Error: expected exactly one top-level directory in {tar_path}, "
                f"found {len(dirs)}: {sorted(d.name for d in dirs)}"
            )
        raw_dir = dirs[0]
        app_dir = work_dir / "app_source"
        raw_dir.rename(app_dir)
        print(f"App directory sanitized: {app_dir}")
        sanitize_tree_permissions(app_dir)

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
            extracted = False
            if asar_path.exists():
                extracted = extract_asar_file(str(asar_path), "icon.png", str(icon_file))
            if not extracted or not icon_file.exists() or icon_file.stat().st_size == 0:
                fallback_icon = repo_root / "assets" / "icon.png"
                if fallback_icon.exists():
                    print(f"Using fallback icon: {fallback_icon}")
                    shutil.copy(fallback_icon, icon_file)

        # Build RPM
        build_rpm(args.package, version, release, args.arch, str(app_dir), str(out_dir), str(desktop_file), str(icon_file))

        # Build DEB if dpkg-deb available
        if shutil.which("dpkg-deb"):
            build_deb(args.package, version, release, args.arch, str(app_dir), str(out_dir), str(desktop_file), str(icon_file))
        else:
            print("Note: dpkg-deb not found on this system, skipping local DEB build.")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
