#!/usr/bin/env python3
import unittest
import sys
import re
from pathlib import Path

# Add scripts directory to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "scripts"))

from build_packages import split_version
from check_upstream import compute_build_plan, validate_upstream, UpstreamError, app_complete
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

        # Packaging revision suffix format
        ver, rel = split_version("2.5.5-4923483625488384.1")
        self.assertEqual(ver, "2.5.5")
        self.assertEqual(rel, "4923483625488384.1")

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
        self.assertTrue((desktop_dir / "antigravity-ide-url-handler.desktop").exists())

        for desktop_file in desktop_dir.glob("*.desktop"):
            content = desktop_file.read_text(encoding="utf-8")
            self.assertIn("[Desktop Entry]", content)
            self.assertIn("Type=Application", content)
            self.assertIn("Exec=", content)
            self.assertIn("Icon=", content)

        ide_content = (desktop_dir / "antigravity-ide.desktop").read_text(encoding="utf-8")
        self.assertIn("application/x-code-workspace;", ide_content)
        self.assertIn("application/x-antigravity-workspace;", ide_content)
        self.assertIn("Keywords=", ide_content)
        self.assertIn("Exec=/usr/bin/antigravity-ide %F", ide_content)

        url_content = (desktop_dir / "antigravity-ide-url-handler.desktop").read_text(encoding="utf-8")
        self.assertIn("NoDisplay=true", url_content)
        self.assertIn("x-scheme-handler/antigravity-ide;", url_content)
        self.assertIn("--open-url %U", url_content)

        hub_content = (desktop_dir / "antigravity.desktop").read_text(encoding="utf-8")
        self.assertIn("Keywords=", hub_content)

        import shutil
        import subprocess
        if shutil.which("desktop-file-validate"):
            res = subprocess.run(["desktop-file-validate"] + [str(f) for f in desktop_dir.glob("*.desktop")], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"desktop-file-validate failed: {res.stderr}")

    def test_file_manager_integrations(self):
        import py_compile
        desktop_dir = repo_root / "desktop"

        # Nautilus & Caja Python Extension
        nautilus_script = desktop_dir / "nautilus" / "open-in-antigravity-ide.py"
        self.assertTrue(nautilus_script.exists())
        content = nautilus_script.read_text(encoding="utf-8")
        self.assertIn("OpenInAntigravityIDE", content)
        self.assertIn("Nautilus", content)
        self.assertIn("Caja", content)
        self.assertIn("Open in Antigravity IDE", content)
        self.assertIn("antigravity-ide", content)
        py_compile.compile(str(nautilus_script), doraise=True)

        # KDE Dolphin KIO Service Menu
        dolphin_file = desktop_dir / "dolphin" / "open-in-antigravity-ide.desktop"
        self.assertTrue(dolphin_file.exists())
        dolphin_content = dolphin_file.read_text(encoding="utf-8")
        self.assertIn("Type=Service", dolphin_content)
        self.assertIn("KonqPopupMenu/Plugin", dolphin_content)
        self.assertIn("openInAntigravityIde", dolphin_content)
        self.assertIn("Exec=antigravity-ide %F", dolphin_content)
        self.assertIn("all/allfiles;", dolphin_content)

        # Nemo Action
        nemo_file = desktop_dir / "nemo" / "open-in-antigravity-ide.nemo_action"
        self.assertTrue(nemo_file.exists())
        nemo_content = nemo_file.read_text(encoding="utf-8")
        self.assertIn("[Nemo Action]", nemo_content)
        self.assertIn("Open in Antigravity IDE", nemo_content)
        self.assertIn("Exec=antigravity-ide %F", nemo_content)

        # Build script packaging recommendations
        build_script = (repo_root / "scripts" / "build_packages.py").read_text(encoding="utf-8")
        self.assertIn("Recommends:     nautilus-python", build_script)
        self.assertIn("python3-nautilus", build_script)

        # Installer integration checks
        installer = (repo_root / "install.sh").read_text(encoding="utf-8")
        self.assertIn("nautilus-python", installer)
        self.assertIn("python3-nautilus", installer)

    def test_llms_txt(self):
        llms_file = repo_root / "llms.txt"
        llms_full_file = repo_root / "llms-full.txt"
        self.assertTrue(llms_file.exists())
        self.assertTrue(llms_full_file.exists())

        llms_content = llms_file.read_text(encoding="utf-8")
        self.assertIn("# Google Antigravity for Linux", llms_content)
        self.assertIn("https://x3m-industries.github.io/antigravity-packages/", llms_content)
        self.assertIn("install.sh", llms_content)

        llms_full_content = llms_full_file.read_text(encoding="utf-8")
        self.assertIn("# Google Antigravity for Linux — Complete Architecture & Operations Guide", llms_full_content)
        self.assertIn("https://x3m-industries.github.io/antigravity-packages/", llms_full_content)
        self.assertIn("dnf install antigravity-ide antigravity", llms_full_content)
        self.assertIn("apt install antigravity-ide antigravity", llms_full_content)

    def test_vercel_apt_redirect_config(self):
        import json
        cfg = json.loads((repo_root / "vercel-apt" / "vercel.json").read_text())
        redirect = cfg["redirects"][0]
        self.assertEqual(redirect["source"], "/deb/pool/main/:file")
        self.assertEqual(
            redirect["destination"],
            "https://github.com/x3m-industries/antigravity-packages/releases/latest/download/:file",
        )
        self.assertFalse(redirect["permanent"])
        rewrite = cfg["rewrites"][0]
        self.assertEqual(rewrite["source"], "/deb/:path*")
        self.assertTrue(rewrite["destination"].startswith("https://x3m-industries.github.io/antigravity-packages/deb/"))

        # Client-facing APT URL must be the redirecting host everywhere
        for rel in ("scripts/generate_repos.sh", "install.sh", "README.md"):
            content = (repo_root / rel).read_text()
            self.assertIn("https://apt.x3m.industries/deb", content, rel)
            self.assertNotIn("x3m-industries.github.io/antigravity-packages/deb", content, rel)

        # The pool is dropped from Pages unless explicitly kept
        gen = (repo_root / "scripts" / "generate_repos.sh").read_text()
        self.assertIn("KEEP_DEB_POOL", gen)

    def test_installer_script(self):
        import subprocess
        install_sh = repo_root / "install.sh"
        self.assertTrue(install_sh.exists())
        content = install_sh.read_text(encoding="utf-8")
        self.assertIn("#!/usr/bin/env bash", content)
        self.assertIn("install_rpm", content)
        self.assertIn("install_deb", content)
        self.assertIn("install_cli", content)
        self.assertIn("antigravity.repo", content)
        self.assertIn("antigravity.sources", content)
        self.assertIn("--cli-only", content)
        self.assertIn("--ide-only", content)
        self.assertIn("--hub-only", content)
        self.assertIn("--all", content)
        self.assertIn("--dry-run", content)
        self.assertIn("--status", content)
        self.assertIn("--uninstall", content)
        self.assertIn("--print-downloads", content)
        self.assertIn("--no-nautilus", content)
        self.assertIn("--nautilus", content)
        self.assertIn("TARGET_USER", content)
        self.assertIn("TARGET_HOME", content)
        self.assertIn("EXISTING_CLI_PATH", content)

        # Validate syntax
        res_syntax = subprocess.run(["bash", "-n", str(install_sh)], capture_output=True, text=True)
        self.assertEqual(res_syntax.returncode, 0, f"bash -n failed: {res_syntax.stderr}")

        # Validate --help execution
        res_help = subprocess.run([str(install_sh), "--help"], capture_output=True, text=True)
        self.assertEqual(res_help.returncode, 0)
        self.assertIn("--cli-only", res_help.stdout)
        self.assertIn("--ide-only", res_help.stdout)
        self.assertIn("--hub-only", res_help.stdout)
        self.assertIn("--all", res_help.stdout)
        self.assertIn("--dry-run", res_help.stdout)
        self.assertIn("--status", res_help.stdout)
        self.assertIn("--uninstall", res_help.stdout)
        self.assertIn("--print-downloads", res_help.stdout)

        # Validate --status execution
        res_status = subprocess.run([str(install_sh), "--status"], capture_output=True, text=True)
        self.assertEqual(res_status.returncode, 0)
        self.assertIn("System Environment:", res_status.stdout)
        self.assertIn("Installed Applications:", res_status.stdout)

        # Validate --print-downloads execution
        res_downloads = subprocess.run([str(install_sh), "--print-downloads"], capture_output=True, text=True)
        self.assertEqual(res_downloads.returncode, 0)
        self.assertIn("Google Antigravity Upstream & Distribution Assets:", res_downloads.stdout)
        self.assertIn("storage.googleapis.com", res_downloads.stdout)

        # Validate --dry-run execution
        res_dry = subprocess.run([str(install_sh), "--dry-run"], capture_output=True, text=True)
        self.assertEqual(res_dry.returncode, 0)
        self.assertIn("Dry run complete", res_dry.stdout)

        # Validate piped execution (curl ... | bash)
        res_pipe = subprocess.run(
            ["bash", "-c", f"cat {install_sh} | bash -s -- --dry-run"],
            capture_output=True, text=True
        )
        self.assertEqual(res_pipe.returncode, 0)
        self.assertIn("Dry run complete", res_pipe.stdout)

        # Validate headless execution without controlling terminal (no /dev/tty errors)
        res_setsid = subprocess.run(
            ["setsid", "bash", str(install_sh), "--dry-run"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True
        )
        self.assertEqual(res_setsid.returncode, 0)
        self.assertNotIn("No such device or address", res_setsid.stderr)

    def test_html_template(self):
        template_file = repo_root / "templates" / "index.html"
        self.assertTrue(template_file.exists())
        html = template_file.read_text(encoding="utf-8")
        self.assertIn("<title>Google Antigravity for Linux", html)
        self.assertIn("switchTab", html)
        self.assertIn("detectOSAndInitTabs", html)
        self.assertIn("X3M Antigravity Packagers", html)
        self.assertIn("E83A 23BC", html)
        self.assertIn("install.sh", html)
        self.assertIn("G-XXTD2B1XB0", html)
        self.assertIn("copy_universal_installer", html)
        self.assertIn("select_distro_tab", html)
        self.assertIn('data-version="ide-semver"', html)
        self.assertIn('data-version="hub-semver"', html)
        self.assertIn("header-version-pill", html)
        self.assertIn("card-version-pill", html)
        self.assertIn('data-tab="cli"', html)
        self.assertIn("Antigravity CLI", html)
        self.assertIn("agy", html)
        self.assertIn("cli-reference", html)
        self.assertIn("bash -s --", html)
        self.assertIn('href="llms.txt"', html)
        self.assertIn("--status", html)
        self.assertIn("--uninstall", html)
        self.assertIn("--print-downloads", html)
        self.assertIn("GNOME Files (Nautilus)", html)
        self.assertIn("terminal-sim-drawer", html)
        self.assertIn("sim-toggle-btn", html)
        self.assertIn("toggleSimDrawer", html)
        self.assertIn("replaySimulation", html)
        self.assertIn("SIM_SCENARIOS", html)
        self.assertIn("prefers-reduced-motion", html)

    def test_docs_template(self):
        docs_file = repo_root / "templates" / "docs.html"
        self.assertTrue(docs_file.exists())
        docs_html = docs_file.read_text(encoding="utf-8")
        self.assertIn("<title>Documentation &amp; CLI Reference — Google Antigravity for Linux", docs_html)
        self.assertIn("Developer &amp; Enterprise Documentation", docs_html)
        self.assertIn("--status", docs_html)
        self.assertIn("--uninstall", docs_html)
        self.assertIn("--print-downloads", docs_html)
        self.assertIn("--no-nautilus", docs_html)
        self.assertIn("open-in-antigravity-ide.py", docs_html)
        self.assertIn("7A48CA4D7E7B6601", docs_html)
        self.assertIn("E83A 23BC", docs_html)
        self.assertIn("G-XXTD2B1XB0", docs_html)
        self.assertIn("debtap", docs_html)

    def test_version_tag_injection(self):
        import sys
        sys.path.insert(0, str(repo_root / "scripts"))
        from inject_versions import parse_release_tag, inject_versions_into_html

        # Test tag parsing
        simulated_tag = "v2.6.0-1234567890123456_hub-2.20.0-9876543210987654"
        parsed = parse_release_tag(simulated_tag)
        self.assertIsNotNone(parsed)
        ide_ver, ide_b, hub_ver, hub_b = parsed
        self.assertEqual(ide_ver, "2.6.0")
        self.assertEqual(ide_b, "1234567890123456")
        self.assertEqual(hub_ver, "2.20.0")
        self.assertEqual(hub_b, "9876543210987654")

        # Test revision tag parsing
        revision_tag = "v2.5.5-4923483625488384.1_hub-2.19.1-6046815158665216"
        parsed_rev = parse_release_tag(revision_tag)
        self.assertIsNotNone(parsed_rev)
        self.assertEqual(parsed_rev[0], "2.5.5")
        self.assertEqual(parsed_rev[1], "4923483625488384.1")
        self.assertEqual(parsed_rev[2], "2.19.1")
        self.assertEqual(parsed_rev[3], "6046815158665216")

        # Test HTML injection
        template_file = repo_root / "templates" / "index.html"
        html = template_file.read_text(encoding="utf-8")
        updated_html = inject_versions_into_html(html, simulated_tag)

        self.assertIn(">v2.6.0<", updated_html)
        self.assertIn(">v2.20.0<", updated_html)
        self.assertIn("Latest packaged release: 2.6.0-1234567890123456", updated_html)
        self.assertIn("Latest packaged release: 2.20.0-9876543210987654", updated_html)

        # Test invalid or placeholder tags
        self.assertIsNone(parse_release_tag("latest"))
        self.assertIsNone(parse_release_tag("vlatest"))
        self.assertEqual(inject_versions_into_html(html, "latest"), html)

    def test_chrome_sandbox_suid_packaging(self):
        build_script = (repo_root / "scripts" / "build_packages.py").read_text(encoding="utf-8")
        install_script = (repo_root / "install.sh").read_text(encoding="utf-8")
        smoke_script = (repo_root / "scripts" / "smoke_test.sh").read_text(encoding="utf-8")

        # Verify RPM spec sets 4755 in %install and %post
        self.assertIn('chmod 4755 "%{{buildroot}}{install_dest}/chrome-sandbox"', build_script)
        self.assertIn('chmod 4755 "{install_dest}/chrome-sandbox"', build_script)

        # Verify DEB sets 4755 in staging and in postinst
        self.assertIn('chmod 4755 "/usr/share/{package_name}/chrome-sandbox"', build_script)
        self.assertIn('chown root:root "/usr/share/{package_name}/chrome-sandbox"', build_script)

        # Verify install.sh enforces 4755 root:root
        self.assertIn("fix_chrome_sandbox()", install_script)
        self.assertIn('chmod 4755 "${target}"', install_script)
        self.assertIn('chown root:root "${target}"', install_script)

        # Verify smoke test validates 4755
        self.assertIn('chmod 4755', smoke_script)
        self.assertIn('-rwsr-xr-x', smoke_script)
        self.assertIn('perms=$(stat -c "%a" "$cs")', smoke_script)
        self.assertIn('expected 4755', smoke_script)

    # ------------------------------------------------------------------
    # check_upstream: build planning
    # ------------------------------------------------------------------
    IDE_VER = "2.5.5-4923483625488384"
    HUB_VER = "2.19.1-6046815158665216"

    def _upstream(self, **overrides):
        up = {
            "antigravity": {
                "version_full": self.HUB_VER,
                "url_x64": "https://example/hub-x64.tar.gz",
                "url_arm64": "https://example/hub-arm.tar.gz",
            },
            "antigravity-ide": {
                "version_full": self.IDE_VER,
                "url_x64": "https://example/ide-x64.tar.gz",
                "url_arm64": "https://example/ide-arm.tar.gz",
            },
        }
        for key, value in overrides.items():
            pkg, field = key.split("__")
            up[pkg.replace("_", "-")][field] = value
        return up

    def _assets(self, ide=None, hub=None):
        ide = ide or self.IDE_VER
        hub = hub or self.HUB_VER
        return [
            f"antigravity-ide-{ide}.x86_64.rpm", f"antigravity-ide-{ide}.aarch64.rpm",
            f"antigravity-ide_{ide}_amd64.deb", f"antigravity-ide_{ide}_arm64.deb",
            f"antigravity-{hub}.x86_64.rpm", f"antigravity-{hub}.aarch64.rpm",
            f"antigravity_{hub}_amd64.deb", f"antigravity_{hub}_arm64.deb",
        ]

    def test_build_plan_nothing_to_do(self):
        # Regression: this path used to crash with UnboundLocalError (has_update unset)
        plan = compute_build_plan(self._upstream(), "v-prev", self._assets(), {})
        self.assertFalse(plan["has_update"])
        self.assertFalse(plan["ide_needs_build"])
        self.assertFalse(plan["hub_needs_build"])
        self.assertEqual(plan["tag_name"], f"v{self.IDE_VER}_hub-{self.HUB_VER}")

    def test_build_plan_single_app_update(self):
        up = self._upstream(antigravity__version_full="2.20.0-111")
        plan = compute_build_plan(up, "v-prev", self._assets(), {})
        self.assertTrue(plan["has_update"])
        self.assertTrue(plan["hub_needs_build"])
        self.assertFalse(plan["ide_needs_build"])
        self.assertEqual(plan["hub_version"], "2.20.0-111")
        self.assertEqual(plan["tag_name"], f"v{self.IDE_VER}_hub-2.20.0-111")

    def test_build_plan_incomplete_release_triggers_rebuild(self):
        # A previous release missing e.g. the arm64 deb must not count as "present"
        assets = [a for a in self._assets() if not a.endswith("_arm64.deb") or "ide" not in a]
        plan = compute_build_plan(self._upstream(), "v-prev", assets, {})
        self.assertTrue(plan["ide_needs_build"])
        self.assertFalse(plan["hub_needs_build"])

    def test_build_plan_first_release(self):
        plan = compute_build_plan(self._upstream(), "", [], {})
        self.assertTrue(plan["has_update"])
        self.assertTrue(plan["ide_needs_build"])
        self.assertTrue(plan["hub_needs_build"])

    def test_build_plan_reuses_published_revision(self):
        # IDE was re-rolled as revision .2 earlier; the tag/version must reflect what is shipped
        assets = self._assets(ide=f"{self.IDE_VER}.2")
        up = self._upstream(antigravity__version_full="2.20.0-111")
        plan = compute_build_plan(up, "v-prev", assets, {})
        self.assertFalse(plan["ide_needs_build"])
        self.assertEqual(plan["ide_version"], f"{self.IDE_VER}.2")
        self.assertEqual(plan["tag_name"], f"v{self.IDE_VER}.2_hub-2.20.0-111")

    def test_build_plan_force_flags_and_revision(self):
        plan = compute_build_plan(self._upstream(), "v-prev", self._assets(), {"FORCE_IDE": "true"})
        self.assertTrue(plan["ide_needs_build"])
        self.assertFalse(plan["hub_needs_build"])

        # Revision applies to the forced app only
        plan = compute_build_plan(self._upstream(), "v-prev", self._assets(),
                                  {"FORCE_HUB": "true", "PKG_REVISION": "1"})
        self.assertTrue(plan["hub_needs_build"])
        self.assertEqual(plan["hub_version"], f"{self.HUB_VER}.1")
        self.assertFalse(plan["ide_needs_build"])
        self.assertEqual(plan["ide_version"], self.IDE_VER)

        # Revision without a forced app re-rolls both
        plan = compute_build_plan(self._upstream(), "v-prev", self._assets(), {"PKG_REVISION": "3"})
        self.assertEqual(plan["ide_version"], f"{self.IDE_VER}.3")
        self.assertEqual(plan["hub_version"], f"{self.HUB_VER}.3")
        self.assertTrue(plan["has_update"])

        plan = compute_build_plan(self._upstream(), "v-prev", self._assets(), {"FORCE_BUILD": "1"})
        self.assertTrue(plan["ide_needs_build"] and plan["hub_needs_build"])

    def test_build_plan_rejects_incomplete_upstream(self):
        # A partial scrape must never produce a release (e.g. tag "..._hub-None")
        for override in (
            {"antigravity__version_full": None},
            {"antigravity__url_arm64": None},
            {"antigravity_ide__url_x64": None},
        ):
            with self.assertRaises(UpstreamError):
                compute_build_plan(self._upstream(**override), "v-prev", self._assets(), {})
        with self.assertRaises(UpstreamError):
            validate_upstream({"antigravity": {}, "antigravity-ide": {}})

    def test_app_complete_does_not_confuse_hub_and_ide(self):
        assets = self._assets()
        self.assertTrue(app_complete("antigravity", self.HUB_VER, assets))
        self.assertTrue(app_complete("antigravity-ide", self.IDE_VER, assets))
        only_ide = [a for a in assets if "ide" in a]
        self.assertFalse(app_complete("antigravity", self.HUB_VER, only_ide))

    # ------------------------------------------------------------------
    # Release / repository safety nets
    # ------------------------------------------------------------------
    def test_verify_packages_script(self):
        import subprocess
        import tempfile
        script = repo_root / "scripts" / "verify_packages.sh"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            res = subprocess.run([str(script), tmp], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)

            for name in self._assets():
                (tmp_path / name).write_bytes(b"")
            res = subprocess.run([str(script), tmp], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr)

            # Removing any single package must be detected (hub rpm must not be satisfied by the ide rpm)
            (tmp_path / f"antigravity-{self.HUB_VER}.aarch64.rpm").unlink()
            res = subprocess.run([str(script), tmp], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("antigravity-[0-9]*.aarch64.rpm", res.stderr)

    def test_signing_is_mandatory_in_ci(self):
        gen = (repo_root / "scripts" / "generate_repos.sh").read_text(encoding="utf-8")
        self.assertIn("REQUIRE_SIGNING", gen)
        self.assertIn("repomd.xml.asc", gen)
        self.assertIn("repo_gpgcheck=1", gen)
        self.assertNotIn("2>/dev/null || true", gen.split("Generating DEB Repository Metadata")[1].split("Generate Release file")[0])

        publish = (repo_root / ".github" / "workflows" / "build-and-publish.yml").read_text(encoding="utf-8")
        pages = (repo_root / ".github" / "workflows" / "deploy-pages.yml").read_text(encoding="utf-8")
        for wf in (publish, pages):
            self.assertIn("REQUIRE_SIGNING: 'true'", wf)
            self.assertIn("GPG_PRIVATE_KEY secret is not set", wf)
            self.assertIn("verify_packages.sh", wf)
            self.assertIn("check_pages_size.sh", wf)
            self.assertIn('group: "packages-and-pages"', wf)
            self.assertNotIn("bun-version: latest", wf)
        self.assertNotIn("|| true", publish.split("Reuse prebuilt Antigravity Hub packages")[1].split("# Build Antigravity IDE")[0])
        self.assertIn("--draft", publish)
        self.assertNotIn('gh release delete "', publish)  # never delete a live release before its replacement exists

    def test_package_dependencies(self):
        build_script = (repo_root / "scripts" / "build_packages.py").read_text(encoding="utf-8")
        # Electron needs libgbm; soname-based RPM deps resolve on Fedora and openSUSE
        self.assertIn("libgbm.so.1()(64bit)", build_script)
        self.assertIn("libgtk-3.so.0()(64bit)", build_script)
        self.assertIn("libgbm1", build_script)
        self.assertIn("libasound2t64 | libasound2", build_script)
        self.assertIn("%defattr(-,root,root,-)", build_script)
        self.assertIn("Installed-Size", build_script)
        self.assertIn('filter="tar"', build_script)

    def test_smoke_test_is_strict(self):
        smoke = (repo_root / "scripts" / "smoke_test.sh").read_text(encoding="utf-8")
        self.assertIn("SMOKE_ARCH", smoke)
        self.assertIn("not found", smoke)  # ldd unresolved-library check
        self.assertNotIn("rpm -q antigravity || true", smoke)
        self.assertNotIn("dpkg -s antigravity 2>/dev/null || true", smoke)

    def test_installer_does_not_duplicate_packaged_files(self):
        installer = (repo_root / "install.sh").read_text(encoding="utf-8")
        for marker in ("NAUTILUS_EOF", "KDE_EOF", "NEMO_EOF"):
            self.assertNotIn(marker, installer)

    def test_astro_site_components(self):
        site_dir = repo_root / "site"
        self.assertTrue(site_dir.exists())

        config_file = site_dir / "src" / "data" / "siteConfig.ts"
        self.assertTrue(config_file.exists())
        config_content = config_file.read_text(encoding="utf-8")
        self.assertIn("7A48CA4D7E7B6601", config_content)
        self.assertIn("E83A 23BC", config_content)
        self.assertIn("parseReleaseTag", config_content)

        index_astro = site_dir / "src" / "pages" / "index.astro"
        docs_astro = site_dir / "src" / "pages" / "docs.astro"
        self.assertTrue(index_astro.exists())
        self.assertTrue(docs_astro.exists())

        astro_config = site_dir / "astro.config.mjs"
        self.assertTrue(astro_config.exists())
        self.assertIn("format: 'file'", astro_config.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
