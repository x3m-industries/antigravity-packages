#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Google Antigravity & Antigravity IDE — Universal Linux Installer
# Maintained by X3M Industries (https://github.com/x3m-industries/antigravity-packages)
# ==============================================================================

BOLD="\033[1m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
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

echo -e "${CYAN}"
cat << 'BANNER_EOF'
   ___         __  _                       _ _          
  / _ \___ ___/ /_(_)__  _______ __  _____(_) /___ __   
 / // / _ `/ _  / / / _\/ __/ _ `/ |/ / // / __/ // /   
/____/\_,_/\_,_/_/_/_/ /_/  \_,_/|___/\_,_/\__/\_, /    
                                               /___/    
BANNER_EOF
echo -e "${RESET}${BOLD}Google Antigravity & Antigravity IDE Linux Installer${RESET}"
echo -e "Repository: https://x3m-industries.github.io/antigravity-packages/\n"

# 1. Architecture Check
ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64|amd64|aarch64|arm64)
        ;;
    *)
        error "Unsupported system architecture: ${ARCH}. Google Antigravity packages require x86_64 or aarch64 / arm64."
        ;;
esac
info "Detected architecture: ${BOLD}${ARCH}${RESET}"

# 2. Sudo / Root Privilege Check
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo > /dev/null 2>&1; then
        SUDO="sudo"
        info "Running with sudo privileges..."
    else
        error "Root privileges are required to configure package repositories. Please run as root or install sudo."
    fi
fi

# 3. Detect Linux Distribution
if [ ! -f /etc/os-release ]; then
    error "/etc/os-release not found. Cannot determine your Linux distribution."
fi

# shellcheck source=/dev/null
. /etc/os-release

DISTRO_ID="${ID:-unknown}"
DISTRO_LIKE="${ID_LIKE:-}"

info "Detected operating system: ${BOLD}${PRETTY_NAME:-$DISTRO_ID}${RESET}"

# 4. Configure Repositories and Install
install_rpm() {
    info "Configuring DNF/YUM repository..."
    ${SUDO} curl -fsSL https://x3m-industries.github.io/antigravity-packages/rpm/antigravity.repo -o /etc/yum.repos.d/antigravity.repo
    success "Added /etc/yum.repos.d/antigravity.repo"

    info "Installing Antigravity IDE and Antigravity Agent Platform..."
    if command -v dnf > /dev/null 2>&1; then
        ${SUDO} dnf install -y antigravity-ide antigravity
    elif command -v yum > /dev/null 2>&1; then
        ${SUDO} yum install -y antigravity-ide antigravity
    fi
}

install_deb() {
    info "Configuring APT repository..."
    ${SUDO} mkdir -p /etc/apt/keyrings
    ${SUDO} curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.gpg -o /etc/apt/keyrings/antigravity.gpg
    ${SUDO} curl -fsSL https://x3m-industries.github.io/antigravity-packages/deb/antigravity.sources -o /etc/apt/sources.list.d/antigravity.sources
    success "Added /etc/apt/keyrings/antigravity.gpg"
    success "Added /etc/apt/sources.list.d/antigravity.sources"

    info "Updating package lists..."
    ${SUDO} apt-get update

    info "Installing Antigravity IDE and Antigravity Agent Platform..."
    ${SUDO} apt-get install -y antigravity-ide antigravity
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

    info "Installing / updating Antigravity IDE and Antigravity Agent Platform..."
    ${SUDO} zypper --non-interactive install -y antigravity-ide antigravity
}

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

echo ""
success "Installation completed successfully!"
echo -e "\n${BOLD}Quick Start:${RESET}"
echo -e "  • Launch Antigravity IDE:     ${CYAN}antigravity-ide ./my-project${RESET}"
echo -e "  • Launch Antigravity Hub:     ${CYAN}antigravity${RESET}"
echo -e "  • Or find ${BOLD}Antigravity IDE${RESET} in your desktop applications menu."
echo ""
