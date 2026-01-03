#!/bin/bash

# Test script for ar-infra-cli project generation
# This script tests the 'init' command and validates the generated project structure

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TEST_DIR="test-generated-project"
GROUP="dev.razafindratelo"
ARTIFACT="demo"
VERSION="0.0.1"
PROJECT_DIR="demo"

EXPECTED_FILES=(
    "build.gradle"
    "Dockerfile"
    "docker-start.sh"
    ".env.template"
    "format.sh"
    ".gitattributes"
    ".gitignore"
    "google-java-format-1.28.0-all-deps.jar"
    "gradlew"
    "gradlew.bat"
    "Makefile"
    "qodana.yaml"
    ".semgrepignore"
    "settings.gradle"
)

EXPECTED_DIRS=(
    "doc"
    ".github"
    "gradle"
    "src"
)

print_success() {
    echo -e "${GREEN}[PASS] $1${NC}"
}

print_error() {
    echo -e "${RED}[FAIL] $1${NC}"
}

print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

cleanup() {
    if [ -d "$TEST_DIR" ]; then
        print_info "Cleaning up test directory..."
        rm -rf "$TEST_DIR"
    fi
}

check_file_exists() {
    local file="$1"
    if [ -f "$TEST_DIR/$PROJECT_DIR/$file" ]; then
        print_success "File exists: $file"
        return 0
    else
        print_error "File missing: $file"
        return 1
    fi
}

check_dir_exists() {
    local dir="$1"
    if [ -d "$TEST_DIR/$PROJECT_DIR/$dir" ]; then
        print_success "Directory exists: $dir"
        return 0
    else
        print_error "Directory missing: $dir"
        return 1
    fi
}

check_file_executable() {
    local file="$1"
    if [ -x "$TEST_DIR/$PROJECT_DIR/$file" ]; then
        print_success "File is executable: $file"
        return 0
    else
        print_error "File not executable: $file"
        return 1
    fi
}

main() {
    echo "-------------------------------------------------------------------"
    echo "AR-INFRA-CLI Project Generation Test"
    echo "-------------------------------------------------------------------"
    echo ""

    cleanup

    print_info "Creating test directory: $TEST_DIR"
    mkdir -p "$TEST_DIR"

    print_info "Running ar-infra-cli init command..."
    echo ""

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    cd "$TEST_DIR" || exit 1

    if PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH" python -m src.ar_infra.cli.main init \
        --group="$GROUP" \
        --artifact="$ARTIFACT" \
        --version="$VERSION" \
        --path=./ \
        --project-dir="$PROJECT_DIR" \
        --no-features \
        --no-cache; then
        print_success "CLI command executed successfully"
    else
        print_error "CLI command failed"
        cd "$PROJECT_ROOT" || exit 1
        exit 1
    fi

    cd "$PROJECT_ROOT" || exit 1
    echo ""

    if [ ! -d "$TEST_DIR/$PROJECT_DIR" ]; then
        print_error "Project directory was not created!"
        exit 1
    fi
    print_success "Project directory created: $PROJECT_DIR"
    echo ""

    print_info "Checking for expected files..."
    missing_files=0
    for file in "${EXPECTED_FILES[@]}"; do
        if ! check_file_exists "$file"; then
            ((missing_files++))
        fi
    done
    echo ""

    print_info "Checking for expected directories..."
    missing_dirs=0
    for dir in "${EXPECTED_DIRS[@]}"; do
        if ! check_dir_exists "$dir"; then
            ((missing_dirs++))
        fi
    done
    echo ""

    print_info "Checking executable permissions..."
    executables_ok=0
    for exec_file in "docker-start.sh" "format.sh" "gradlew"; do
        if ! check_file_executable "$exec_file"; then
            ((executables_ok++))
        fi
    done
    echo ""

    print_info "Generated project structure:"
    echo ""
    if command -v tree &> /dev/null; then
        tree -L 2 "$TEST_DIR/$PROJECT_DIR"
    else
        ls -lah "$TEST_DIR/$PROJECT_DIR"
    fi
    echo ""

    total_files=$(find "$TEST_DIR/$PROJECT_DIR" -type f | wc -l)
    total_dirs=$(find "$TEST_DIR/$PROJECT_DIR" -type d | wc -l)
    print_info "Total files: $total_files"
    print_info "Total directories: $total_dirs"
    echo ""

    print_info "Validating file contents..."

    # Check build.gradle contains correct group/artifact/version
    if grep -q "$GROUP" "$TEST_DIR/$PROJECT_DIR/build.gradle" && \
       grep -q "$ARTIFACT" "$TEST_DIR/$PROJECT_DIR/build.gradle" && \
       grep -q "$VERSION" "$TEST_DIR/$PROJECT_DIR/build.gradle"; then
        print_success "build.gradle contains correct metadata"
    else
        print_error "build.gradle missing correct metadata"
        ((missing_files++))
    fi
    echo ""

    echo "-------------------------------------------------------------------"
    echo "Test Summary"
    echo "-------------------------------------------------------------------"

    total_errors=$((missing_files + missing_dirs + executables_ok))

    if [ $total_errors -eq 0 ]; then
        print_success "All checks passed!"
        echo ""
        print_info "Keeping test directory for inspection: $TEST_DIR"
        print_info "Run 'rm -rf $TEST_DIR' to clean up"
        exit 0
    else
        print_error "Test failed with $total_errors error(s)"
        echo ""
        print_info "Test directory preserved for debugging: $TEST_DIR"
        exit 1
    fi
}

trap 'if [ $? -ne 0 ]; then print_info "Test directory preserved for debugging: $TEST_DIR"; fi' EXIT

main
