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
  faqs: [
    {
      q: "What is the difference between antigravity-ide and antigravity?",
      a: "Google provides two separate official applications: antigravity-ide (the desktop code editor based on Code OSS) and antigravity (the Agent Hub / Antigravity 2.0 platform). They are versioned separately by Google and packaged independently.",
    },
    {
      q: "How do daily updates work?",
      a: "Our automated pipeline tracks Google's official release CDN daily at 05:00 UTC. When Google publishes a new release, packages are built, cryptographically signed, and pushed to our RPM and DEB repositories. You update via sudo dnf update or sudo apt upgrade.",
    },
    {
      q: "Why choose native RPM or DEB packages over tarball extractors in /opt?",
      a: "Native repositories integrate with your operating system's package database (DNF, APT, Zypper). You get automatic system updates, GPG cryptographic signature checks, dependency resolution, proper SUID sandboxing, and clean uninstallation.",
    },
    {
      q: "Does this include GNOME Files (Nautilus) right-click integration?",
      a: "Yes! The installer automatically sets up a Nautilus extension allowing you to right-click any file, directory, or folder background and select 'Open in Antigravity IDE'.",
    },
    {
      q: "Can I install only the terminal CLI without the desktop apps?",
      a: "Yes! Run the installer with --cli-only. It installs Google's official terminal agent into ~/.local/bin/agy without requiring root or sudo permissions.",
    },
    {
      q: "How is security and package integrity guaranteed?",
      a: "Every RPM and APT release is cryptographically signed using our dedicated GPG key (Key ID: 7A48CA4D7E7B6601). Upstream Google binaries are checked against official SHA256 checksums.",
    },
  ],
};
