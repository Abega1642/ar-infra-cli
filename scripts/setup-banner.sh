#!/usr/bin/env bash

# AR-INFRA Banner Setup Script
# Installs Node.js dependencies and generates the CLI banner

set -euo pipefail

readonly LOG_INFO="\033[0;36m"
readonly LOG_SUCCESS="\033[0;32m"
readonly LOG_ERROR="\033[0;31m"
readonly LOG_RESET="\033[0m"

log_info() {
    echo -e "${LOG_INFO}[INFO]${LOG_RESET} $*"
}

log_success() {
    echo -e "${LOG_SUCCESS}[SUCCESS]${LOG_RESET} $*"
}

log_error() {
    echo -e "${LOG_ERROR}[ERROR]${LOG_RESET} $*" >&2
}

check_node() {
    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
        return 1
    fi

    local node_version
    node_version=$(node --version | sed 's/v//' | cut -d. -f1)

    if [ "$node_version" -lt 18 ]; then
        log_error "Node.js version 18 or higher is required. Current version: $(node --version)"
        return 1
    fi

    log_success "Node.js $(node --version) detected"
    return 0
}

check_npm() {
    if ! command -v npm >/dev/null 2>&1; then
        log_error "npm is not installed"
        return 1
    fi

    log_success "npm $(npm --version) detected"
    return 0
}

install_dependencies() {
    log_info "Installing Node.js dependencies..."

    if [ ! -f "package.json" ]; then
        log_error "package.json not found in project root"
        return 1
    fi

    if npm install --silent; then
        log_success "Dependencies installed"
        return 0
    else
        log_error "npm install failed"
        return 1
    fi
}

generate_banner() {
    log_info "Generating banner with npm run generate-banner..."

    # Just run the npm script directly - it handles everything
    if npm run generate-banner; then
        log_success "Banner generation complete"
        return 0
    else
        log_error "Banner generation failed"
        return 1
    fi
}

verify_banner() {
    local banner_path="src/ar_infra/cli/resources/banner.txt"

    if [ ! -f "$banner_path" ]; then
        log_error "Banner file was not generated at $banner_path"
        return 1
    fi

    if [ ! -s "$banner_path" ]; then
        log_error "Banner file is empty"
        return 1
    fi

    # Check if it contains ANSI escape sequences
    if ! grep -q $'\x1b\[' "$banner_path"; then
        log_error "Banner file does not contain ANSI escape sequences"
        return 1
    fi

    local file_size=$(stat -c%s "$banner_path" 2>/dev/null || stat -f%z "$banner_path" 2>/dev/null)
    log_success "Banner file verified at $banner_path (${file_size} bytes)"

    return 0
}

main() {
    log_info "Starting AR-INFRA banner setup..."
    echo

    if ! check_node || ! check_npm; then
        log_error "Prerequisites check failed"
        return 1
    fi
    echo

    if ! install_dependencies; then
        log_error "Dependency installation failed"
        return 1
    fi
    echo

    if ! generate_banner; then
        log_error "Banner generation failed"
        return 1
    fi
    echo

    if ! verify_banner; then
        log_error "Banner verification failed"
        return 1
    fi
    echo

    log_success "Banner setup completed successfully!"
    log_info "You can now run: python -m src.ar_infra.cli.main"
    return 0
}

main "$@"
