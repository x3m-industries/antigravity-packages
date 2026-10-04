#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Google Antigravity Suite — Universal Linux Installer & Package Manager
# Installs Antigravity IDE, Antigravity Hub, Antigravity CLI ('agy'),
# and native desktop integrations (MIME schemes, GNOME Nautilus extension).
# Maintained by X3M Industries (https://github.com/x3m-industries/antigravity-packages)
# ==============================================================================

BOLD="\033[1m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
DIM="\033[2m"
RESET="\033[0m"

info() {
    echo -e "${BLUE}==>${RESET} ${BOLD}$*${RESET}"
}

success() {
    echo -e "${GREEN}✓${RESET} ${BOLD}$*${RESET}"
}

warn() {
    echo -e "${YELLOW}Warning:${RESET} $*"
}

error() {
    echo -e "${RED}Error:${RESET} $*" >&2
    exit 1
}

show_banner() {
    echo -e "${CYAN}"
    cat << 'BANNER_EOF'
    ___    _   ___________ ________  ___ _    _____________  __
   /   |  / | / /_  __/  _/ ____/ __ \/   | |  / /  _/_  __/\ \/ /
  / /| | /  |/ / / /  / // / __/ /_/ / /| | | / // /  / /    \  / 
 / ___ |/ /|  / / / _/ // /_/ / _, _/ ___ | |/ // /  / /     / /  
/_/  |_/_/ |_/ /_/ /___/\____/_/ |_/_/  |_|___/___/ /_/     /_/   
BANNER_EOF
    echo -e "${RESET}${BOLD}Google Antigravity Linux Universal Installer & Package Manager${RESET}"
    echo -e "Repository: https://x3m-industries.github.io/antigravity-packages/\n"
}

show_help() {
    echo -e "${BOLD}Usage:${RESET} install.sh [options]"
    echo ""
    echo -e "${BOLD}Installation Modes:${RESET}"
    echo "  -y, --yes, --non-interactive  Run silently without interactive prompts (installs defaults)"
    echo "  --all                         Install all components (IDE, Hub, CLI, desktop integrations)"
    echo "  --cli-only                    Install only the Antigravity CLI ('agy') (no sudo required)"
    echo "  --ide-only                    Install only the Antigravity IDE (code editor)"
    echo "  --hub-only                    Install only the Antigravity Hub (agent platform)"
    echo "  --no-cli                      Skip Antigravity CLI installation"
    echo "  --no-ide                      Skip Antigravity IDE installation"
    echo "  --no-hub                      Skip Antigravity Hub installation"
    echo "  --no-nautilus                 Skip GNOME Files / Nautilus context menu integration"
    echo "  --dry-run                     Show what would be installed and exit without making changes"
    echo ""
    echo -e "${BOLD}Inspection & Maintenance:${RESET}"
    echo "  --status                      Show installed components, versions, and repository health"
    echo "  --print-downloads             Print official Google tarballs & package download URLs"
    echo "  --uninstall                   Cleanly remove helper-configured repositories & packages"
    echo "  -h, --help                    Display this help menu"
    echo ""
    echo -e "${BOLD}Examples:${RESET}"
    echo "  curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash"
    echo "  curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- -y"
    echo "  curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --status"
    echo "  curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --uninstall"
    echo ""
}

# 1. Architecture Check
ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64|amd64|aarch64|arm64)
        ;;
    *)
        error "Unsupported system architecture: ${ARCH}. Google Antigravity packages require x86_64 or aarch64 / arm64."
        ;;
esac

# 2. Prerequisite Check (curl)
ensure_curl() {
    if ! command -v curl > /dev/null 2>&1; then
        if [ "$(id -u)" -eq 0 ]; then
            info "'curl' is not installed. Installing curl..."
            if command -v apt-get > /dev/null 2>&1; then
                apt-get update -qq && apt-get install -y --no-install-recommends curl ca-certificates
            elif command -v dnf > /dev/null 2>&1; then
                dnf install -y curl ca-certificates
            elif command -v zypper > /dev/null 2>&1; then
                zypper --non-interactive install -y curl ca-certificates
            elif command -v pacman > /dev/null 2>&1; then
                pacman -Sy --noconfirm curl ca-certificates
            else
                error "'curl' is required but could not be installed automatically. Please install curl."
            fi
        elif command -v sudo > /dev/null 2>&1; then
            info "'curl' is not installed. Attempting to install via sudo..."
            if command -v apt-get > /dev/null 2>&1; then
                sudo apt-get update -qq && sudo apt-get install -y --no-install-recommends curl ca-certificates
            elif command -v dnf > /dev/null 2>&1; then
                sudo dnf install -y curl ca-certificates
            elif command -v zypper > /dev/null 2>&1; then
                sudo zypper --non-interactive install -y curl ca-certificates
            else
                error "'curl' is required but not installed. Please install curl and re-run."
            fi
        else
            error "'curl' is required but not installed. Please install curl (e.g. 'sudo apt install curl' or 'sudo dnf install curl')."
        fi
    fi
}
ensure_curl

# 3. Target User & Home Directory Resolution
if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
    TARGET_USER="${SUDO_USER}"
    TARGET_HOME=$(getent passwd "${TARGET_USER}" 2>/dev/null | cut -d: -f6 || true)
    if [ -z "${TARGET_HOME}" ] || [ "${TARGET_HOME}" = "/" ]; then
        if [ -d "/home/${TARGET_USER}" ]; then
            TARGET_HOME="/home/${TARGET_USER}"
        else
            TARGET_HOME="${HOME:-/root}"
        fi
    fi
else
    TARGET_USER="${USER:-$(id -un 2>/dev/null || echo "user")}"
    TARGET_HOME="${HOME:-/root}"
fi

# Component selection defaults
INSTALL_IDE=true
INSTALL_HUB=true
INSTALL_CLI=true
INSTALL_NAUTILUS=true
INTERACTIVE=true
DRY_RUN=false
DO_STATUS=false
DO_UNINSTALL=false
DO_PRINT_DOWNLOADS=false

# Parse Command-Line Arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        --status)
            DO_STATUS=true
            INTERACTIVE=false
            ;;
        --uninstall)
            DO_UNINSTALL=true
            INTERACTIVE=false
            ;;
        --print-downloads)
            DO_PRINT_DOWNLOADS=true
            INTERACTIVE=false
            ;;
        --dry-run)
            INTERACTIVE=false
            DRY_RUN=true
            ;;
        -y|--yes|--non-interactive)
            INTERACTIVE=false
            ;;
        --all)
            INTERACTIVE=false
            INSTALL_IDE=true
            INSTALL_HUB=true
            INSTALL_CLI=true
            INSTALL_NAUTILUS=true
            ;;
        --cli-only)
            INTERACTIVE=false
            INSTALL_IDE=false
            INSTALL_HUB=false
            INSTALL_CLI=true
            INSTALL_NAUTILUS=false
            ;;
        --ide-only)
            INTERACTIVE=false
            INSTALL_IDE=true
            INSTALL_HUB=false
            INSTALL_CLI=false
            ;;
        --hub-only)
            INTERACTIVE=false
            INSTALL_IDE=false
            INSTALL_HUB=true
            INSTALL_CLI=false
            INSTALL_NAUTILUS=false
            ;;
        --no-cli)
            INTERACTIVE=false
            INSTALL_CLI=false
            ;;
        --no-ide)
            INTERACTIVE=false
            INSTALL_IDE=false
            INSTALL_NAUTILUS=false
            ;;
        --no-hub)
            INTERACTIVE=false
            INSTALL_HUB=false
            ;;
        --no-nautilus)
            INSTALL_NAUTILUS=false
            ;;
        --nautilus)
            INSTALL_NAUTILUS=true
            ;;
        --cli)
            INTERACTIVE=false
            INSTALL_CLI=true
            ;;
        --ide)
            INTERACTIVE=false
            INSTALL_IDE=true
            ;;
        --hub)
            INTERACTIVE=false
            INSTALL_HUB=true
            ;;
        -h|--help)
            show_banner
            show_help
            exit 0
            ;;
        *)
            error "Unknown argument: $1. Run 'install.sh --help' for usage."
            ;;
    esac
    shift
done

# Check non-interactive environment variables
if [ -n "${CI:-}" ] || [ -n "${NONINTERACTIVE:-}" ] || [ "${DEBIAN_FRONTEND:-}" = "noninteractive" ]; then
    INTERACTIVE=false
fi

# Detect installed versions for components
INSTALLED_IDE_VER=""
if command -v antigravity-ide > /dev/null 2>&1 || [ -x /usr/bin/antigravity-ide ]; then
    if command -v rpm > /dev/null 2>&1 && rpm -q antigravity-ide > /dev/null 2>&1; then
        INSTALLED_IDE_VER=$(rpm -q --qf "%{VERSION}" antigravity-ide 2>/dev/null || true)
    elif command -v dpkg-query > /dev/null 2>&1 && dpkg-query -W -f='${Version}' antigravity-ide > /dev/null 2>&1; then
        INSTALLED_IDE_VER=$(dpkg-query -W -f='${Version}' antigravity-ide 2>/dev/null || true)
    else
        INSTALLED_IDE_VER="installed"
    fi
fi

INSTALLED_HUB_VER=""
if command -v antigravity > /dev/null 2>&1 || [ -x /usr/bin/antigravity ]; then
    if command -v rpm > /dev/null 2>&1 && rpm -q antigravity > /dev/null 2>&1; then
        INSTALLED_HUB_VER=$(rpm -q --qf "%{VERSION}" antigravity 2>/dev/null || true)
    elif command -v dpkg-query > /dev/null 2>&1 && dpkg-query -W -f='${Version}' antigravity > /dev/null 2>&1; then
        INSTALLED_HUB_VER=$(dpkg-query -W -f='${Version}' antigravity 2>/dev/null || true)
    else
        INSTALLED_HUB_VER="installed"
    fi
fi

EXISTING_CLI_PATH=""
INSTALLED_CLI_VER=""
if [ -x "${TARGET_HOME}/.local/bin/agy" ]; then
    EXISTING_CLI_PATH="${TARGET_HOME}/.local/bin/agy"
    INSTALLED_CLI_VER=$("${EXISTING_CLI_PATH}" --version 2>/dev/null || true)
elif command -v agy > /dev/null 2>&1; then
    EXISTING_CLI_PATH="$(command -v agy)"
    INSTALLED_CLI_VER=$("${EXISTING_CLI_PATH}" --version 2>/dev/null || true)
fi

# Detect Linux Distribution
DISTRO_ID="unknown"
DISTRO_LIKE=""
PRETTY_NAME="Linux"
if [ -f /etc/os-release ]; then
    # shellcheck source=/dev/null
    . /etc/os-release
    DISTRO_ID="${ID:-unknown}"
    DISTRO_LIKE="${ID_LIKE:-}"
fi

# Sudo / Root Privilege Check
SUDO=""
check_sudo() {
    if [ "$(id -u)" -ne 0 ]; then
        if command -v sudo > /dev/null 2>&1; then
            SUDO="sudo"
        else
            error "Root privileges are required for this action. Please run as root or install sudo."
        fi
    fi
}

# ------------------------------------------------------------------------------
# Action: --status (Show installed components, versions, and repository health)
# ------------------------------------------------------------------------------
show_status() {
    show_banner
    echo -e "${BOLD}System Environment:${RESET}"
    echo -e "  • OS:             ${PRETTY_NAME} (${ARCH})"
    echo -e "  • User:           ${TARGET_USER} (${TARGET_HOME})"
    echo ""

    echo -e "${BOLD}Installed Applications:${RESET}"
    if [ -n "${INSTALLED_IDE_VER}" ]; then
        echo -e "  • ${GREEN}Antigravity IDE:${RESET}       Installed (${BOLD}v${INSTALLED_IDE_VER}${RESET}) -> $(command -v antigravity-ide 2>/dev/null || echo '/usr/bin/antigravity-ide')"
    else
        echo -e "  • ${DIM}Antigravity IDE:${RESET}       Not installed"
    fi

    if [ -n "${INSTALLED_HUB_VER}" ]; then
        echo -e "  • ${GREEN}Antigravity Hub:${RESET}       Installed (${BOLD}v${INSTALLED_HUB_VER}${RESET}) -> $(command -v antigravity 2>/dev/null || echo '/usr/bin/antigravity')"
    else
        echo -e "  • ${DIM}Antigravity Hub:${RESET}       Not installed"
    fi

    if [ -n "${EXISTING_CLI_PATH}" ]; then
        echo -e "  • ${GREEN}Antigravity CLI ('agy'):${RESET} Installed (${BOLD}${INSTALLED_CLI_VER:-active}${RESET}) -> ${EXISTING_CLI_PATH}"
    else
        echo -e "  • ${DIM}Antigravity CLI ('agy'):${RESET} Not installed"
    fi
    echo ""

    echo -e "${BOLD}Repository Configuration:${RESET}"
    if [ -f /etc/yum.repos.d/antigravity.repo ]; then
        echo -e "  • ${GREEN}RPM / DNF Repo:${RESET}        /etc/yum.repos.d/antigravity.repo ${GREEN}[Configured]${RESET}"
    elif [ -f /etc/apt/sources.list.d/antigravity.sources ] || [ -f /etc/apt/sources.list.d/antigravity.list ]; then
        echo -e "  • ${GREEN}DEB / APT Sources:${RESET}     /etc/apt/sources.list.d/antigravity.sources ${GREEN}[Configured]${RESET}"
        if [ -f /etc/apt/keyrings/antigravity.gpg ]; then
            echo -e "  • ${GREEN}APT GPG Keyring:${RESET}       /etc/apt/keyrings/antigravity.gpg ${GREEN}[Verified]${RESET}"
        fi
    elif command -v zypper > /dev/null 2>&1 && zypper repos antigravity > /dev/null 2>&1; then
        echo -e "  • ${GREEN}Zypper Repo:${RESET}           antigravity ${GREEN}[Configured]${RESET}"
    else
        echo -e "  • ${YELLOW}Package Repositories:${RESET}  No native repository configured yet."
    fi
    echo ""

    echo -e "${BOLD}Desktop & File Manager Integration:${RESET}"
    [ -f /usr/share/applications/antigravity-ide.desktop ] && echo -e "  • ${GREEN}IDE Desktop Entry:${RESET}     /usr/share/applications/antigravity-ide.desktop"
    [ -f /usr/share/applications/antigravity.desktop ] && echo -e "  • ${GREEN}Hub Desktop Entry:${RESET}     /usr/share/applications/antigravity.desktop"
    if [ -f /usr/share/nautilus-python/extensions/open-in-antigravity-ide.py ]; then
        echo -e "  • ${GREEN}GNOME Nautilus Menu:${RESET}   /usr/share/nautilus-python/extensions/open-in-antigravity-ide.py ${GREEN}[Active]${RESET}"
    else
        echo -e "  • ${DIM}GNOME Nautilus Menu:${RESET}   Not installed"
    fi
    echo ""
}

# ------------------------------------------------------------------------------
# Action: --print-downloads (Print official Google tarballs & package URLs)
# ------------------------------------------------------------------------------
print_downloads() {
    show_banner
    echo -e "${BOLD}Google Antigravity Upstream & Distribution Assets:${RESET}\n"
    echo -e "  ${BOLD}Architecture Detected:${RESET} ${ARCH}\n"

    echo -e "  ${BOLD}1. Official Google Antigravity Hub (Agent Platform):${RESET}"
    echo -e "     • x86_64:  ${CYAN}https://storage.googleapis.com/antigravity-public/antigravity-hub/latest/linux-x64/Antigravity.tar.gz${RESET}"
    echo -e "     • aarch64: ${CYAN}https://storage.googleapis.com/antigravity-public/antigravity-hub/latest/linux-arm/Antigravity.tar.gz${RESET}"
    echo ""

    echo -e "  ${BOLD}2. Official Google Antigravity IDE (AI Code Editor):${RESET}"
    echo -e "     • Web:     ${CYAN}https://antigravity.google/download${RESET}"
    echo ""

    echo -e "  ${BOLD}3. Official Google Antigravity CLI ('agy'):${RESET}"
    echo -e "     • Script:  ${CYAN}https://antigravity.google/cli/install.sh${RESET}"
    echo ""

    echo -e "  ${BOLD}4. X3M Industries Native Linux Packages & Repositories:${RESET}"
    echo -e "     • Releases: ${CYAN}https://github.com/x3m-industries/antigravity-packages/releases/latest${RESET}"
    echo -e "     • DNF Repo: ${CYAN}https://x3m-industries.github.io/antigravity-packages/rpm/${RESET}"
    echo -e "     • APT Repo: ${CYAN}https://x3m-industries.github.io/antigravity-packages/deb/${RESET}"
    echo -e "     • LLM Context: ${CYAN}https://x3m-industries.github.io/antigravity-packages/llms.txt${RESET}"
    echo ""
}

# ------------------------------------------------------------------------------
# Action: --uninstall (Cleanly remove helper-configured repos, packages & files)
# ------------------------------------------------------------------------------
do_uninstall() {
    show_banner
    check_sudo

    if [ "${INTERACTIVE}" = true ]; then
        echo -e "${YELLOW}${BOLD}Are you sure you want to uninstall Google Antigravity Linux components?${RESET}"
        echo -e "This will remove native RPM/DEB packages, repository configs, GPG keys, and desktop integrations."
        echo -e "User settings and code projects in home directories will remain completely untouched.\n"
        printf "Proceed with uninstallation? [y/N]: "
        read -r confirm || true
        case "${confirm}" in
            y|Y|yes|YES) ;;
            *) echo "Uninstallation aborted."; exit 0 ;;
        esac
    fi

    info "Removing Google Antigravity packages..."
    if command -v dnf > /dev/null 2>&1; then
        ${SUDO} dnf remove -y antigravity antigravity-ide 2>/dev/null || true
    elif command -v yum > /dev/null 2>&1; then
        ${SUDO} yum remove -y antigravity antigravity-ide 2>/dev/null || true
    elif command -v apt-get > /dev/null 2>&1; then
        ${SUDO} apt-get remove -y antigravity antigravity-ide 2>/dev/null || true
    elif command -v zypper > /dev/null 2>&1; then
        ${SUDO} zypper --non-interactive remove -y antigravity antigravity-ide 2>/dev/null || true
    fi

    info "Removing repository configurations and GPG keyrings..."
    ${SUDO} rm -f /etc/yum.repos.d/antigravity.repo
    ${SUDO} rm -f /etc/apt/sources.list.d/antigravity.sources
    ${SUDO} rm -f /etc/apt/sources.list.d/antigravity.list
    ${SUDO} rm -f /etc/apt/keyrings/antigravity.gpg
    if command -v zypper > /dev/null 2>&1 && zypper repos antigravity > /dev/null 2>&1; then
        ${SUDO} zypper --non-interactive removerepo antigravity 2>/dev/null || true
    fi

    info "Removing GNOME Nautilus integration..."
    ${SUDO} rm -f /usr/share/nautilus-python/extensions/open-in-antigravity-ide.py

    if [ -x "${TARGET_HOME}/.local/bin/agy" ]; then
        info "Removing Antigravity CLI ('agy') at ${TARGET_HOME}/.local/bin/agy..."
        rm -f "${TARGET_HOME}/.local/bin/agy"
    fi

    # Refresh desktop & icon caches
    if command -v update-desktop-database > /dev/null 2>&1; then
        ${SUDO} update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
    fi
    if command -v gtk-update-icon-cache > /dev/null 2>&1; then
        ${SUDO} gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
    fi

    echo ""
    success "Google Antigravity packages, repositories, and desktop integrations have been cleanly removed."
    info "User configuration files in ${TARGET_HOME}/.config and project files were left intact."
    exit 0
}

# Check explicit action flags
if [ "${DO_STATUS}" = true ]; then
    show_status
    exit 0
fi

if [ "${DO_PRINT_DOWNLOADS}" = true ]; then
    print_downloads
    exit 0
fi

if [ "${DO_UNINSTALL}" = true ]; then
    do_uninstall
    exit 0
fi

show_banner

# 4. Interactive Selection (if TTY is available and interactive mode is not disabled)
if [ "${INTERACTIVE}" = true ]; then
    if ! (exec 3</dev/tty) 2>/dev/null && [ ! -t 0 ]; then
        info "Non-interactive environment detected. Proceeding with default components (all)..."
    else
        echo -e "${BOLD}Select components to install / update:${RESET}\n"

        status_ide="${DIM}[Not installed]${RESET}"
        [ -n "${INSTALLED_IDE_VER}" ] && status_ide="${GREEN}[Installed: v${INSTALLED_IDE_VER}]${RESET}"

        status_hub="${DIM}[Not installed]${RESET}"
        [ -n "${INSTALLED_HUB_VER}" ] && status_hub="${GREEN}[Installed: v${INSTALLED_HUB_VER}]${RESET}"

        status_cli="${DIM}[Not installed]${RESET}"
        [ -n "${INSTALLED_CLI_VER}" ] && status_cli="${GREEN}[Installed: v${INSTALLED_CLI_VER}]${RESET}"

        echo -e "  ${BOLD}[1] Antigravity IDE${RESET}        AI-first standalone code editor (RPM/DEB)     ${status_ide}"
        echo -e "  ${BOLD}[2] Antigravity Hub${RESET}        Antigravity 2.0 desktop agent hub (RPM/DEB)   ${status_hub}"
        echo -e "  ${BOLD}[3] Antigravity CLI (agy)${RESET}  Terminal agent with auto-updating             ${status_cli}"
        echo ""

        user_choice=""
        if (exec 3</dev/tty) 2>/dev/null; then
            printf "Enter selection [Default: 1, 2, 3 (All)] or press ENTER: "
            read -r user_choice < /dev/tty || true
        else
            read -r -p "Enter selection [Default: 1, 2, 3 (All)] or press ENTER: " user_choice || true
        fi
        echo ""

        choice_clean=$(echo "${user_choice}" | tr ',' ' ' | tr -d '\r')
        if [ -n "${choice_clean// /}" ]; then
            INSTALL_IDE=false
            INSTALL_HUB=false
            INSTALL_CLI=false

            for item in ${choice_clean}; do
                case "${item}" in
                    1|ide)
                        INSTALL_IDE=true
                        ;;
                    2|hub)
                        INSTALL_HUB=true
                        ;;
                    3|cli|agy)
                        INSTALL_CLI=true
                        ;;
                    all|a)
                        INSTALL_IDE=true
                        INSTALL_HUB=true
                        INSTALL_CLI=true
                        ;;
                    q|quit|exit|none)
                        echo "Installation aborted by user."
                        exit 0
                        ;;
                    *)
                        warn "Unknown component selection: '${item}' (ignored)"
                        ;;
                esac
            done
        fi
    fi
fi

# Ensure at least one component was selected
if [ "${INSTALL_IDE}" = false ] && [ "${INSTALL_HUB}" = false ] && [ "${INSTALL_CLI}" = false ]; then
    warn "No components were selected for installation. Exiting."
    exit 0
fi

info "Installation plan:"
[ "${INSTALL_IDE}" = true ] && echo -e "  • ${CYAN}Antigravity IDE${RESET} (Native package & desktop launcher)"
[ "${INSTALL_HUB}" = true ] && echo -e "  • ${CYAN}Antigravity Hub${RESET} (Antigravity 2.0 agent platform)"
[ "${INSTALL_CLI}" = true ] && echo -e "  • ${CYAN}Antigravity CLI ('agy')${RESET} (Terminal agent with auto-updater)"
[ "${INSTALL_IDE}" = true ] && [ "${INSTALL_NAUTILUS}" = true ] && echo -e "  • ${CYAN}GNOME Nautilus Integration${RESET} ('Open in Antigravity IDE' context menu)"
echo ""

if [ "${DRY_RUN}" = true ]; then
    info "Dry run complete. No changes were made."
    exit 0
fi

# Sudo check for system package installation
if [ "${INSTALL_IDE}" = true ] || [ "${INSTALL_HUB}" = true ]; then
    check_sudo
    if [ "$(id -u)" -ne 0 ]; then
        info "Requesting sudo privileges to configure package repositories..."
    fi
fi

# 5. Package Installation Functions
fix_chrome_sandbox() {
    local target="$1"
    if [ -f "${target}" ]; then
        ${SUDO} chown root:root "${target}" 2>/dev/null || true
        ${SUDO} chmod 4755 "${target}" 2>/dev/null || true
    fi
}

install_rpm() {
    info "Configuring DNF/YUM repository..."
    ${SUDO} curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo
    success "Added /etc/yum.repos.d/antigravity.repo"

    local pkgs=()
    [ "${INSTALL_IDE}" = true ] && pkgs+=("antigravity-ide")
    [ "${INSTALL_HUB}" = true ] && pkgs+=("antigravity")

    if [ ${#pkgs[@]} -gt 0 ]; then
        info "Installing ${pkgs[*]}..."
        if command -v dnf > /dev/null 2>&1; then
            ${SUDO} dnf install -y "${pkgs[@]}"
        elif command -v yum > /dev/null 2>&1; then
            ${SUDO} yum install -y "${pkgs[@]}"
        fi
        fix_chrome_sandbox "/usr/share/antigravity-ide/chrome-sandbox"
        fix_chrome_sandbox "/usr/share/antigravity/chrome-sandbox"
    fi
}

install_deb() {
    info "Configuring APT repository..."
    ${SUDO} mkdir -p /etc/apt/keyrings
    ${SUDO} curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
    ${SUDO} curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources
    success "Added /etc/apt/keyrings/antigravity.gpg"
    success "Added /etc/apt/sources.list.d/antigravity.sources"

    local pkgs=()
    [ "${INSTALL_IDE}" = true ] && pkgs+=("antigravity-ide")
    [ "${INSTALL_HUB}" = true ] && pkgs+=("antigravity")

    if [ ${#pkgs[@]} -gt 0 ]; then
        info "Updating package lists..."
        ${SUDO} apt-get update

        info "Installing ${pkgs[*]}..."
        ${SUDO} apt-get install -y "${pkgs[@]}"
        fix_chrome_sandbox "/usr/share/antigravity-ide/chrome-sandbox"
        fix_chrome_sandbox "/usr/share/antigravity/chrome-sandbox"
    fi
}

install_zypper() {
    info "Configuring Zypper repository for openSUSE..."
    if ${SUDO} zypper repos antigravity > /dev/null 2>&1; then
        ${SUDO} zypper --non-interactive modifyrepo --enable --refresh antigravity
    else
        ${SUDO} zypper --non-interactive addrepo -f https://x3m-industries.github.io/antigravity-packages/rpm/ antigravity
    fi
    ${SUDO} rpm --import https://x3m-industries.github.io/antigravity-packages/rpm/RPM-GPG-KEY-antigravity
    success "Configured zypper repository 'antigravity'"

    local pkgs=()
    [ "${INSTALL_IDE}" = true ] && pkgs+=("antigravity-ide")
    [ "${INSTALL_HUB}" = true ] && pkgs+=("antigravity")

    if [ ${#pkgs[@]} -gt 0 ]; then
        info "Installing ${pkgs[*]}..."
        ${SUDO} zypper --non-interactive install -y "${pkgs[@]}"
        fix_chrome_sandbox "/usr/share/antigravity-ide/chrome-sandbox"
        fix_chrome_sandbox "/usr/share/antigravity/chrome-sandbox"
    fi
}

install_nautilus_extension() {
    [ "${INSTALL_IDE}" = true ] || return 0
    [ "${INSTALL_NAUTILUS}" = true ] || return 0

    if ! command -v nautilus > /dev/null 2>&1 && [ ! -d /usr/share/nautilus-python ]; then
        return 0
    fi

    info "Configuring GNOME Files / Nautilus right-click context menu..."
    if command -v apt-get > /dev/null 2>&1 && ! dpkg -s python3-nautilus > /dev/null 2>&1; then
        info "Installing python3-nautilus package for file manager extension..."
        ${SUDO} apt-get install -y --no-install-recommends python3-nautilus 2>/dev/null || true
    fi

    ${SUDO} mkdir -p /usr/share/nautilus-python/extensions
    ${SUDO} tee /usr/share/nautilus-python/extensions/open-in-antigravity-ide.py > /dev/null << 'NAUTILUS_EOF'
#!/usr/bin/env python3
"""
Nautilus (GNOME Files) context-menu extension for Antigravity IDE.
Adds right-click options:
- "Open in Antigravity IDE" on files and directories.
- "Open Folder in Antigravity IDE" on folder backgrounds.
Maintained by X3M Industries (https://github.com/x3m-industries/antigravity-packages)
"""

import subprocess
from urllib.parse import unquote, urlparse
from gi.repository import GObject, Nautilus


class OpenInAntigravityIDE(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()

    def _get_path(self, file_info):
        if not file_info:
            return None
        uri = file_info.get_uri()
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            return None
        return unquote(parsed.path)

    def get_file_items(self, *args):
        files = args[-1] if args else []
        if not files or len(files) != 1:
            return []

        path = self._get_path(files[0])
        if not path:
            return []

        item = Nautilus.MenuItem(
            name="OpenInAntigravityIDE::open",
            label="Open in Antigravity IDE",
            tip="Open this file or folder in Antigravity IDE",
            icon="antigravity-ide",
        )
        item.connect("activate", lambda _menu_item: subprocess.Popen(["antigravity-ide", path]))
        return [item]

    def get_background_items(self, *args):
        folder = args[-1] if args else None
        if not folder:
            return []

        path = self._get_path(folder)
        if not path:
            return []

        item = Nautilus.MenuItem(
            name="OpenInAntigravityIDE::open_background",
            label="Open Folder in Antigravity IDE",
            tip="Open current folder in Antigravity IDE",
            icon="antigravity-ide",
        )
        item.connect("activate", lambda _menu_item: subprocess.Popen(["antigravity-ide", path]))
        return [item]
NAUTILUS_EOF
    ${SUDO} chmod 0644 /usr/share/nautilus-python/extensions/open-in-antigravity-ide.py
    success "Configured Nautilus context menu ('Open in Antigravity IDE')"
}

install_cli() {
    info "Checking Antigravity CLI ('agy')..."

    if [ -n "${EXISTING_CLI_PATH}" ]; then
        success "Antigravity CLI is already installed at ${EXISTING_CLI_PATH} (${INSTALLED_CLI_VER:-installed})"
        info "Skipping download (Antigravity CLI automatically self-updates in the background during normal usage)"
        return 0
    fi

    info "Installing Antigravity CLI ('agy') via official Google installer into ${TARGET_HOME}/.local/bin/agy..."
    if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
        if command -v su > /dev/null 2>&1; then
            su - "${TARGET_USER}" -c "curl -fsSL https://antigravity.google/cli/install.sh | bash"
        elif command -v runuser > /dev/null 2>&1; then
            runuser -u "${TARGET_USER}" -- bash -c "curl -fsSL https://antigravity.google/cli/install.sh | bash"
        else
            error "Neither 'su' nor 'runuser' is available to switch to user '${TARGET_USER}'."
        fi
    else
        curl -fsSL https://antigravity.google/cli/install.sh | bash
    fi
    success "Antigravity CLI installed successfully"
}

# 6. Execute System Package Installations (IDE / Hub)
if [ "${INSTALL_IDE}" = true ] || [ "${INSTALL_HUB}" = true ]; then
    case "${DISTRO_ID}" in
        fedora|rhel|centos|rocky|almalinux|amzn|nobara)
            install_rpm
            ;;
        ubuntu|debian|linuxmint|pop|elementary|zorin|kali|raspbian)
            install_deb
            ;;
        opensuse*|sles)
            install_zypper
            ;;
        arch|manjaro|endeavouros)
            error "Arch Linux detected. Please install via manual package extraction or stay tuned for our upcoming AUR package."
            ;;
        *)
            if echo "${DISTRO_LIKE}" | grep -qE "fedora|rhel|centos"; then
                install_rpm
            elif echo "${DISTRO_LIKE}" | grep -qE "debian|ubuntu"; then
                install_deb
            elif echo "${DISTRO_LIKE}" | grep -qE "suse"; then
                install_zypper
            else
                error "Unsupported distribution: '${DISTRO_ID}'. You can download raw RPM or DEB packages from https://github.com/x3m-industries/antigravity-packages/releases"
            fi
            ;;
    esac

    # Install Nautilus extension if enabled
    install_nautilus_extension
fi

# 7. Execute CLI Installation (User-space)
if [ "${INSTALL_CLI}" = true ]; then
    install_cli
fi

# 8. Post-Install Summary & Guidance
echo ""
success "Installation completed successfully!"
echo -e "\n${BOLD}Quick Start:${RESET}"
[ "${INSTALL_IDE}" = true ] && echo -e "  • Launch Antigravity IDE:     ${CYAN}antigravity-ide ./my-project${RESET}"
[ "${INSTALL_HUB}" = true ] && echo -e "  • Launch Antigravity Hub:     ${CYAN}antigravity${RESET}"
if [ "${INSTALL_CLI}" = true ]; then
    echo -e "  • Launch Antigravity CLI:     ${CYAN}agy${RESET}"
    if [[ ":${PATH}:" != *":${TARGET_HOME}/.local/bin:"* ]]; then
        echo -e "\n${YELLOW}Note:${RESET} Ensure ${BOLD}${TARGET_HOME}/.local/bin${RESET} is in your shell PATH. If 'agy' is not found, add to your shell profile:"
        echo -e "  ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
    fi
fi
if [ "${INSTALL_IDE}" = true ] && [ -f /usr/share/nautilus-python/extensions/open-in-antigravity-ide.py ]; then
    echo -e "  • GNOME Files / Nautilus:     Restart Nautilus ('nautilus -q') to see the right-click menu."
fi
echo -e "\n${BOLD}Maintenance & Inspection:${RESET}"
echo -e "  • Check Status:               ${CYAN}curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --status${RESET}"
echo -e "  • System Updates:             Run ${CYAN}sudo dnf update${RESET} or ${CYAN}sudo apt update && sudo apt upgrade${RESET}"
echo -e "\n${YELLOW}⭐ If this saved you time, please star the project on GitHub:${RESET}"
echo -e "  ${BOLD}https://github.com/x3m-industries/antigravity-packages${RESET}\n"
