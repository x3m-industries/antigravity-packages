export interface ReleaseVersions {
  ideSemver: string;
  ideBuild: string;
  hubSemver: string;
  hubBuild: string;
}

export function parseReleaseTag(tag?: string): ReleaseVersions {
  const defaultVersions: ReleaseVersions = {
    ideSemver: "2.5.5",
    ideBuild: "4923483625488384",
    hubSemver: "2.19.1",
    hubBuild: "6046815158665216",
  };

  if (!tag || tag === "latest" || tag === "vlatest") {
    return defaultVersions;
  }

  // Combined tag: v<ide_ver>-<ide_build>_hub-<hub_ver>-<hub_build>
  const m = tag.match(/^v([0-9\.]+)(?:-([0-9a-zA-Z\.\-]+))?_hub-([0-9\.]+)(?:-([0-9a-zA-Z\.\-]+))?/);
  if (m && m[1] && m[3]) {
    return {
      ideSemver: m[1],
      ideBuild: m[2] || defaultVersions.ideBuild,
      hubSemver: m[3],
      hubBuild: m[4] || defaultVersions.hubBuild,
    };
  }

  // Single tag fallback: v<ver>-<build>
  const mSimple = tag.match(/^v([0-9\.]+)(?:-([0-9a-zA-Z\.\-]+))?/);
  if (mSimple && mSimple[1]) {
    return {
      ideSemver: mSimple[1],
      ideBuild: mSimple[2] || defaultVersions.ideBuild,
      hubSemver: mSimple[1],
      hubBuild: mSimple[2] || defaultVersions.hubBuild,
    };
  }

  return defaultVersions;
}

// Read RELEASE_TAG from build environment if passed
const rawTag = (typeof process !== "undefined" ? process.env.RELEASE_TAG : undefined) || import.meta.env.RELEASE_TAG;
export const currentVersions = parseReleaseTag(rawTag);

export const siteConfig = {
  siteUrl: "https://x3m-industries.github.io/antigravity-packages/",
  baseUrl: "/antigravity-packages/",
  title: "Google Antigravity for Linux — 1-Command Installer & Native Repositories (DNF, APT)",
  docsTitle: "Documentation & CLI Reference — Google Antigravity for Linux",
  description:
    "Install Google Antigravity 2.0, Antigravity IDE & CLI on Linux with 1 command. Native DNF & APT repositories with automatic daily updates for Fedora, Ubuntu, Debian, Arch & openSUSE.",
  author: {
    name: "Steven Ceuppens · X3M Industries",
    url: "https://x3m.industries",
    github: "https://github.com/stevenceuppens",
    linkedin: "https://www.linkedin.com/in/stevenceuppens/",
    x: "https://x.com/stevenceuppens",
  },
  gpg: {
    keyId: "7A48CA4D7E7B6601",
    fingerprint: "E83A 23BC 57FE 6953 E4B5  F465 7A48 CA4D 7E7B 6601",
    maintainer: "X3M Antigravity Packagers <packaging@x3m.industries>",
    rpmKeyUrl: "https://x3m-industries.github.io/antigravity-packages/RPM-GPG-KEY-antigravity",
    debKeyringUrl: "https://x3m-industries.github.io/antigravity-packages/antigravity.gpg",
  },
  repo: {
    githubUrl: "https://github.com/x3m-industries/antigravity-packages",
    releasesUrl: "https://github.com/x3m-industries/antigravity-packages/releases",
    installerUrl: "https://x3m-industries.github.io/antigravity-packages/install.sh",
  },
  commands: {
    universal: {
      id: "universal",
      label: "⚡ Universal 1-Liner (Recommended)",
      cmd: "curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash",
      desc: "One command auto-detects Fedora, Ubuntu, Debian, openSUSE, RHEL & Arch with native packages.",
    },
    cli: {
      id: "cli",
      label: "Antigravity CLI ('agy')",
      cmd: "curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --cli-only",
      desc: "Install only Google Antigravity CLI ('agy') into ~/.local/bin/agy (no sudo needed).",
    },
  },
  homeFaqs: [
    {
      q: "What is the difference between antigravity-ide and antigravity?",
      a: `Google provides two separate official applications for Linux:<br>
• <strong><code>antigravity-ide</code></strong>: The official Google AI code editor with visual diff viewer, terminal integration, application menu launcher, and <code>antigravity-ide://</code> browser OAuth handlers.<br>
• <strong><code>antigravity</code></strong>: Google's official Agent Hub (Antigravity 2.0) interface for configuring and orchestrating autonomous coding agents. Google's standalone terminal agent (<strong><code>agy</code></strong>) is installed separately via user-space CLI.<br>
Because Google versions them separately (e.g. IDE 2.5.5 vs Hub 2.19.1), X3M Industries packages them as two independent native packages so you can install both or either one.`,
    },
    {
      q: "How do updates work?",
      a: `Our automated pipeline tracks Google's official release CDN daily at 05:00 UTC. When Google publishes an update, packages are built, cryptographically signed, and deployed to our repositories. You receive them automatically during your normal system upgrades (<code>sudo dnf update</code> or <code>sudo apt upgrade</code>).`,
    },
    {
      q: "Why should I use native RPM or DEB packages instead of extracting tarballs to /opt?",
      a: `Unlike basic community scripts that unpack tarballs to <code>/opt</code> without package manager integration, native RPM and DEB packages integrate directly with DNF, APT, and Zypper. You receive cryptographically signed packages with GPG, automated system updates, proper dependency resolution, hardened Chromium sandboxing permissions, and clean uninstallation without leaving orphaned files.`,
    },
    {
      q: "Does this include GNOME Files (Nautilus) right-click integration?",
      a: `Yes! When Antigravity IDE is installed, the installer automatically configures a GNOME Files (Nautilus) Python extension. You can right-click any file, project directory, or directory background in Nautilus and select <strong>"Open in Antigravity IDE"</strong>.`,
    },
  ],
  docsFaqs: [
    {
      q: "What is the difference between antigravity-ide and antigravity?",
      a: `Google provides two distinct desktop applications for Linux:<br>
• <strong><code>antigravity-ide</code></strong>: The official Google AI code editor based on Code OSS with application menu launchers, diff viewer, and <code>antigravity-ide://</code> browser OAuth handlers.<br>
• <strong><code>antigravity</code></strong>: Google's official Agent Hub (Antigravity 2.0) interface for configuring and orchestrating autonomous coding agents. Google's standalone terminal agent (<code>agy</code>) is installed separately into user-space (<code>~/.local/bin/agy</code>).`,
    },
    {
      q: "How do daily automated updates work?",
      a: `A GitHub Actions automated cron workflow checks Google's official download CDN daily at 05:00 UTC. Whenever Google pushes a new release, packages for both <code>x86_64</code> and <code>aarch64</code> are built, sanitized, signed, tested in Fedora/Ubuntu containers, and deployed. You receive them via standard system updates (<code>dnf update</code> or <code>apt upgrade</code>).`,
    },
    {
      q: "Why should I use native RPM or DEB packages instead of extracting tarballs to /opt?",
      a: `Manual tutorials often instruct users to unpack Google tarballs into <code>/opt/antigravity</code>. While this seems simple initially, it creates severe real-world problems:<br>
• <strong>Broken In-App Auto-Updates:</strong> Because <code>/opt</code> is owned by <code>root</code>, Electron's unprivileged auto-updater fails silently with permission errors, trapping you in manual update cycles.<br>
• <strong>Missing High-Res Icons:</strong> Google bundles the Hub's icon inside <code>app.asar</code>. Manual installers get stuck with generic desktop gear icons. Our packages dynamically parse the ASAR header and register native 512x512 icons.<br>
• <strong>Broken Google OAuth Logins:</strong> Manual desktop files omit URL protocol handlers (<code>antigravity://</code> and <code>antigravity-ide://</code>), causing browser login redirects to fail.<br>
• <strong>Hardened Chromium Sandboxing:</strong> Ubuntu 24.04+ restricts unprivileged user namespaces via AppArmor. Without hardened <code>4755 root:root</code> permissions on <code>chrome-sandbox</code>, Electron apps crash.<br>
• <strong>Package Manager Integration:</strong> Native RPM &amp; DEB packages update seamlessly via <code>apt upgrade</code> or <code>dnf update</code>, verify GPG signatures, resolve shared libraries, and uninstall cleanly without orphaned files.`,
    },
    {
      q: "How do I update Google Antigravity IDE in Ubuntu or Debian?",
      a: `Run <code>sudo apt update &amp;&amp; sudo apt install --only-upgrade antigravity-ide antigravity</code>, or simply perform your regular system upgrade with <code>sudo apt update &amp;&amp; sudo apt upgrade</code>.`,
    },
    {
      q: "Does this include GNOME Files (Nautilus) right-click integration?",
      a: `Yes! When Antigravity IDE is installed, the installer sets up a Nautilus extension allowing you to right-click any file, directory, or empty folder background and select <strong>"Open in Antigravity IDE"</strong>.`,
    },
    {
      q: "Are ARM64 / aarch64 systems supported?",
      a: `Yes! Both <code>x86_64</code> (Intel/AMD) and <code>aarch64</code> (ARM64, Raspberry Pi 4/5 64-bit, Ampere, Apple Silicon Linux VMs) RPM and DEB packages are natively built and published for every release.`,
    },
    {
      q: "Is it safe to run the universal installer more than once?",
      a: `Yes, the universal installer is completely idempotent. Running it multiple times safely refreshes repository definitions and GPG keys without creating duplicates, and upgrades your applications to the latest upstream release.`,
    },
    {
      q: "How do I check installation status or cleanly uninstall?",
      a: `Run <code>curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --status</code> to inspect installed components, or pass <code>--uninstall</code> to cleanly remove packages, repos, and extensions without touching your personal projects.`,
    },
  ],
};
