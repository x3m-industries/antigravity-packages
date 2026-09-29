#!/usr/bin/env python3
import unittest
import sys
import re
from pathlib import Path

# Add scripts directory to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "scripts"))

from build_packages import split_version
from stats import analyze_downloads


class TestPackagingLogic(unittest.TestCase):
    def test_split_version(self):
        # Full build number format
        ver, rel = split_version("2.5.5-4923483625488384")
        self.assertEqual(ver, "2.5.5")
        self.assertEqual(rel, "4923483625488384")

        # Simple semver format
        ver, rel = split_version("2.18.1")
        self.assertEqual(ver, "2.18.1")
        self.assertEqual(rel, "1")

        # Multi-hyphen format
        ver, rel = split_version("1.0.0-beta.1-12345")
        self.assertEqual(ver, "1.0.0")
        self.assertEqual(rel, "beta.1-12345")

    def test_upstream_regex_matching(self):
        sample_html = """
        <a href="https://storage.googleapis.com/antigravity-public/antigravity-hub/2.18.1-4945794252537856/linux-x64/Antigravity.tar.gz">Download</a>
        <a href="https://storage.googleapis.com/antigravity-public/antigravity-hub/2.18.1-4945794252537856/linux-arm/Antigravity.tar.gz">Download ARM</a>
        <a href="https://edgedl.me.gvt1.com/edgedl/release2/chrome/2.5.5-4923483625488384/linux-x64/Antigravity%20IDE.tar.gz">IDE x64</a>
        <a href="https://edgedl.me.gvt1.com/edgedl/release2/chrome/2.5.5-4923483625488384/linux-arm/Antigravity+IDE.tar.gz">IDE ARM</a>
        """

        hub_match = re.search(r'https://storage\.googleapis\.com/antigravity-public/antigravity-hub/([0-9a-zA-Z\.\-]+)/linux-x64/Antigravity\.tar\.gz', sample_html)
        hub_arm_match = re.search(r'https://storage\.googleapis\.com/antigravity-public/antigravity-hub/([0-9a-zA-Z\.\-]+)/linux-arm/Antigravity\.tar\.gz', sample_html)
        ide_match = re.search(r'https://edgedl\.me\.gvt1\.com/edgedl/release2/[^\"\' ]+/([0-9a-zA-Z\.\-]+)/linux-x64/Antigravity(?:%20|\+)IDE\.tar\.gz', sample_html)
        ide_arm_match = re.search(r'https://edgedl\.me\.gvt1\.com/edgedl/release2/[^\"\' ]+/([0-9a-zA-Z\.\-]+)/linux-arm/Antigravity(?:%20|\+)IDE\.tar\.gz', sample_html)

        self.assertIsNotNone(hub_match)
        self.assertEqual(hub_match.group(1), "2.18.1-4945794252537856")

        self.assertIsNotNone(hub_arm_match)
        self.assertEqual(hub_arm_match.group(1), "2.18.1-4945794252537856")

        self.assertIsNotNone(ide_match)
        self.assertEqual(ide_match.group(1), "2.5.5-4923483625488384")

        self.assertIsNotNone(ide_arm_match)
        self.assertEqual(ide_arm_match.group(1), "2.5.5-4923483625488384")

    def test_analyze_downloads(self):
        mock_releases = [
            {
                "tag_name": "v1.0.0",
                "assets": [
                    {"name": "antigravity-1.0.0.x86_64.rpm", "download_count": 50, "size": 1024 * 1024 * 100},
                    {"name": "antigravity-1.0.0.aarch64.rpm", "download_count": 10, "size": 1024 * 1024 * 90},
                    {"name": "antigravity_1.0.0_amd64.deb", "download_count": 20, "size": 1024 * 1024 * 80},
                    {"name": "antigravity-ide-1.0.0.x86_64.rpm", "download_count": 30, "size": 1024 * 1024 * 150},
                    {"name": "antigravity-ide_1.0.0_arm64.deb", "download_count": 5, "size": 1024 * 1024 * 140},
                ]
            }
        ]

        stats = analyze_downloads(mock_releases)
        self.assertEqual(stats["total_downloads"], 115)
        self.assertEqual(stats["by_format"]["rpm"], 90)
        self.assertEqual(stats["by_format"]["deb"], 25)
        self.assertEqual(stats["by_package"]["antigravity"], 80)
        self.assertEqual(stats["by_package"]["antigravity-ide"], 35)
        self.assertEqual(stats["by_arch"]["x86_64"], 100)
        self.assertEqual(stats["by_arch"]["aarch64"], 15)

    def test_desktop_files(self):
        desktop_dir = repo_root / "desktop"
        self.assertTrue((desktop_dir / "antigravity.desktop").exists())
        self.assertTrue((desktop_dir / "antigravity-ide.desktop").exists())

        for desktop_file in desktop_dir.glob("*.desktop"):
            content = desktop_file.read_text(encoding="utf-8")
            self.assertIn("[Desktop Entry]", content)
            self.assertIn("Type=Application", content)
            self.assertIn("Exec=", content)
            self.assertIn("Icon=", content)

        import shutil
        import subprocess
        if shutil.which("desktop-file-validate"):
            res = subprocess.run(["desktop-file-validate"] + [str(f) for f in desktop_dir.glob("*.desktop")], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"desktop-file-validate failed: {res.stderr}")

    def test_installer_script(self):
        install_sh = repo_root / "install.sh"
        self.assertTrue(install_sh.exists())
        content = install_sh.read_text(encoding="utf-8")
        self.assertIn("#!/usr/bin/env bash", content)
        self.assertIn("install_rpm", content)
        self.assertIn("install_deb", content)
        self.assertIn("antigravity.repo", content)
        self.assertIn("antigravity.sources", content)

    def test_html_template(self):
        template_file = repo_root / "templates" / "index.html"
        self.assertTrue(template_file.exists())
        html = template_file.read_text(encoding="utf-8")
        self.assertIn("<title>", html)
        self.assertIn("switchTab", html)
        self.assertIn("detectOSAndInitTabs", html)
        self.assertIn("X3M Antigravity Packagers", html)
        self.assertIn("E83A 23BC", html)
        self.assertIn("install.sh", html)


if __name__ == "__main__":
    unittest.main()
