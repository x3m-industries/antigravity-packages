#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Google Antigravity Suite — Universal Linux Installer
# Installs Antigravity IDE, Antigravity Hub, and Antigravity CLI ('agy')
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
    echo -e "${RESET}${BOLD}Google Antigravity Linux Universal Installer${RESET}"
    echo -e "Repository: https://x3m-industries.github.io/antigravity-packages/\n"
}

show_help() {
    echo -e "${BOLD}Usage:${RESET} install.sh [options]"
    echo ""
    echo -e "${BOLD}Options:${RESET}"
    echo "  -y, --yes, --non-interactive  Run silently without interactive prompts (installs defaults)"
    echo "  --all                         Install all components (IDE, Hub, CLI)"
    echo "  --cli-only                    Install only the Antigravity CLI ('agy') (no sudo required)"
    echo "  --ide-only                    Install only the Antigravity IDE (code editor)"
    echo "  --hub-only                    Install only the Antigravity Hub (agent platform)"
    echo "  --no-cli                      Skip Antigravity CLI installation"
    echo "  --no-ide                      Skip Antigravity IDE installation"
    echo "  --no-hub                      Skip Antigravity Hub installation"
    echo "  --dry-run                     Show what would be installed and exit without making changes"
    echo "  -h, --help                    Display this help menu"
    echo ""
    echo -e "${BOLD}Examples:${RESET}"
    echo "  curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash"
    echo "  curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- --cli-only"
    echo "  curl -fsSL https://x3m-industries.github.io/antigravity-packages/install.sh | bash -s -- -y"
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
INTERACTIVE=true
DRY_RUN=false

# Parse Command-Line Arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
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
            ;;
        --cli-only)
            INTERACTIVE=false
            INSTALL_IDE=false
            INSTALL_HUB=false
            INSTALL_CLI=true
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
            ;;
        --no-cli)
            INTERACTIVE=false
            INSTALL_CLI=false
            ;;
        --no-ide)
            INTERACTIVE=false
            INSTALL_IDE=false
            ;;
        --no-hub)
            INTERACTIVE=false
            INSTALL_HUB=false
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

show_banner

# 4. Interactive Selection (if TTY is available and interactive mode is not disabled)
if [ "${INTERACTIVE}" = true ]; then
    # Check if a terminal device is accessible
    if [ ! -c /dev/tty ] && [ ! -t 0 ]; then
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

        # Read choice from /dev/tty to support 'curl ... | bash'
        user_choice=""
        if [ -c /dev/tty ]; then
            printf "Enter selection [Default: 1, 2, 3 (All)] or press ENTER: "
            read -r user_choice < /dev/tty || true
        else
            read -r -p "Enter selection [Default: 1, 2, 3 (All)] or press ENTER: " user_choice || true
        fi
        echo ""

        # Normalize choice
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
[ "${INSTALL_IDE}" = true ] && echo -e "  • ${CYAN}Antigravity IDE${RESET}"
[ "${INSTALL_HUB}" = true ] && echo -e "  • ${CYAN}Antigravity Hub${RESET}"
[ "${INSTALL_CLI}" = true ] && echo -e "  • ${CYAN}Antigravity CLI ('agy')${RESET}"
echo ""

if [ "${DRY_RUN}" = true ]; then
    info "Dry run complete. No changes were made."
    exit 0
fi

# 5. Sudo / Root Privilege Check (Only required if installing system packages: IDE or Hub)
SUDO=""
check_sudo() {
    if [ "$(id -u)" -ne 0 ]; then
        if command -v sudo > /dev/null 2>&1; then
            SUDO="sudo"
            info "Requesting sudo privileges to configure package repositories..."
        else
            error "Root privileges are required to configure package repositories. Please run as root or install sudo."
        fi
    fi
}

if [ "${INSTALL_IDE}" = true ] || [ "${INSTALL_HUB}" = true ]; then
    check_sudo
fi

# 6. Detect Linux Distribution
if [ ! -f /etc/os-release ]; then
    error "/etc/os-release not found. Cannot determine your Linux distribution."
fi

# shellcheck source=/dev/null
. /etc/os-release

DISTRO_ID="${ID:-unknown}"
DISTRO_LIKE="${ID_LIKE:-}"

info "Detected system: ${BOLD}${PRETTY_NAME:-$DISTRO_ID}${RESET} (${ARCH})"

# 7. Package Installation Functions
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
    fi
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

# 8. Execute System Package Installations (IDE / Hub)
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
            # Fallback to ID_LIKE inspection
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
fi

# 9. Execute CLI Installation (User-space)
if [ "${INSTALL_CLI}" = true ]; then
    install_cli
fi

# 10. Post-Install Summary & Guidance
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
echo -e "\n${YELLOW}⭐ If this saved you time, please star the project on GitHub:${RESET}"
echo -e "  ${BOLD}https://github.com/x3m-industries/antigravity-packages${RESET}\n"
