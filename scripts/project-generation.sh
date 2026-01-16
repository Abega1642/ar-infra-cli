#!/bin/bash

# project-generation.sh - Integration test for ar-infra-cli project generation.
# Tests the 'init' command and validates generated project structure.

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

readonly TEST_DIR="test-generated-project"
readonly GROUP="dev.razafindratelo"
readonly ARTIFACT="demo"
readonly VERSION="0.0.1"
readonly PROJECT_DIR="demo"

readonly EXPECTED_FILES=(
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

readonly EXPECTED_DIRS=(
    "doc"
    ".github"
    "gradle"
    "src"
)

cleanup() {
    if [ -d "$TEST_DIR" ]; then
        print_info "Cleaning up test directory..."
        rm -rf "$TEST_DIR"
    fi
}

check_file_exists() {
    local file="$1"
    local full_path="$TEST_DIR/$PROJECT_DIR/$file"

    if ! validate_path "$full_path" "$TEST_DIR/$PROJECT_DIR"; then
        print_error "Invalid file path: $file"
        return 1
    fi

    if [ -f "$full_path" ] && [ ! -L "$full_path" ]; then
        print_success "File exists: $file"
        return 0
    else
        print_error "File missing or invalid: $file"
        return 1
    fi
}

check_dir_exists() {
    local dir="$1"
    local full_path="$TEST_DIR/$PROJECT_DIR/$dir"

    if ! validate_path "$full_path" "$TEST_DIR/$PROJECT_DIR"; then
        print_error "Invalid directory path: $dir"
        return 1
    fi

    if [ -d "$full_path" ] && [ ! -L "$full_path" ]; then
        print_success "Directory exists: $dir"
        return 0
    else
        print_error "Directory missing or invalid: $dir"
        return 1
    fi
}

check_file_executable() {
    local file="$1"
    local full_path="$TEST_DIR/$PROJECT_DIR/$file"

    if [ -x "$full_path" ]; then
        print_success "File is executable: $file"
        return 0
    else
        print_error "File not executable: $file"
        return 1
    fi
}

validate_file_contents() {
    print_info "Validating file contents..."

    local errors=0
    local build_gradle="$TEST_DIR/$PROJECT_DIR/build.gradle"
    local settings_gradle="$TEST_DIR/$PROJECT_DIR/settings.gradle"

    if grep -q "group.*=.*['\"]$GROUP['\"]" "$build_gradle" || \
       grep -q "$GROUP" "$build_gradle"; then
        print_success "build.gradle contains group metadata"
    else
        print_error "build.gradle missing group metadata"
        ((errors++))
    fi

    if grep -q "rootProject.name.*=.*['\"]$ARTIFACT['\"]" "$settings_gradle" || \
       grep -q "$ARTIFACT" "$settings_gradle"; then
        print_success "settings.gradle contains artifact metadata"
    else
        print_error "settings.gradle missing artifact metadata"
        ((errors++))
    fi

    return $errors
}

run_project_generation() {
    local project_root="$1"

    print_info "Running ar-infra-cli init command..."
    print_info "Project root: $project_root"

    local python_path
    python_path=$(setup_python_path "$project_root")
    print_info "PYTHONPATH: $python_path"

    local cmd=(
        python -m src.ar_infra.cli.main init
        --group="$GROUP"
        --artifact="$ARTIFACT"
        --project-version="$VERSION"
        --path=./
        --project-dir="$PROJECT_DIR"
        --features
        --no-cache
        --skip-github-app
    )

    if PYTHONPATH="$python_path" "${cmd[@]}"; then
        print_success "CLI command executed successfully"
        return 0
    else
        print_error "CLI command failed"
        return 1
    fi
}

display_project_structure() {
    print_info "Generated project structure:"
    echo ""

    if command -v tree &> /dev/null; then
        tree -L 2 "$TEST_DIR/$PROJECT_DIR" || ls -lah "$TEST_DIR/$PROJECT_DIR"
    else
        ls -lah "$TEST_DIR/$PROJECT_DIR"
    fi
    echo ""

    local total_files
    total_files=$(find "$TEST_DIR/$PROJECT_DIR" -type f ! -path "*/.git/*" 2>/dev/null | wc -l)
    local total_dirs
    total_dirs=$(find "$TEST_DIR/$PROJECT_DIR" -type d ! -path "*/.git/*" 2>/dev/null | wc -l)

    print_info "Total files: $total_files"
    print_info "Total directories: $total_dirs"
}

main() {
    local exit_code=0

    echo "********************************************"
    echo "AR-INFRA-CLI Project Generation Test"
    echo "********************************************"
    echo ""

    cleanup

    print_info "Creating test directory: $TEST_DIR"
    mkdir -p "$TEST_DIR"

    local project_root
    project_root=$(get_project_root) || exit 1

    cd "$TEST_DIR" || {
        print_error "Failed to change to test directory"
        exit 1
    }

    if ! run_project_generation "$project_root"; then
        cd "$project_root" || exit 1
        exit 1
    fi

    if is_windows; then
        wait_for_git_unlock "$PROJECT_DIR"
    fi

    cd "$project_root" || {
        print_error "Failed to return to project root"
        exit 1
    }

    echo ""

    if [ ! -d "$TEST_DIR/$PROJECT_DIR" ]; then
        print_error "Project directory was not created!"
        exit 1
    fi
    print_success "Project directory created: $PROJECT_DIR"
    echo ""

    print_info "Checking for expected files..."
    local missing_files=0
    for file in "${EXPECTED_FILES[@]}"; do
        if ! check_file_exists "$file"; then
            ((missing_files++))
        fi
    done
    echo ""

    print_info "Checking for expected directories..."
    local missing_dirs=0
    for dir in "${EXPECTED_DIRS[@]}"; do
        if ! check_dir_exists "$dir"; then
            ((missing_dirs++))
        fi
    done
    echo ""

    if ! is_windows; then
        print_info "Checking executable permissions..."
        local executables_failed=0
        for exec_file in "docker-start.sh" "format.sh" "gradlew"; do
            if ! check_file_executable "$exec_file"; then
                ((executables_failed++))
            fi
        done
        echo ""
    else
        print_info "Skipping executable permission checks on Windows"
        local executables_failed=0
        echo ""
    fi

    display_project_structure
    echo ""

    local content_errors=0
    validate_file_contents || content_errors=$?
    echo ""

    local total_errors=$((missing_files + missing_dirs + executables_failed + content_errors))

    echo "********************************************"
    echo "Test Summary"
    echo "********************************************"

    if [ $total_errors -eq 0 ]; then
        print_success "All checks passed!"
        echo ""
        print_info "Test directory preserved for inspection: $TEST_DIR"
        print_info "Run 'rm -rf $TEST_DIR' to clean up"
        exit_code=0
    else
        print_error "Test failed with $total_errors error(s)"
        echo ""
        print_info "Breakdown:"
        print_info "  Missing files: $missing_files"
        print_info "  Missing directories: $missing_dirs"
        print_info "  Executable permission failures: $executables_failed"
        print_info "  Content validation errors: $content_errors"
        echo ""
        print_info "Test directory preserved for debugging: $TEST_DIR"
        exit_code=1
    fi

    exit $exit_code
}

trap 'if [ $? -ne 0 ]; then print_warning "Test directory preserved for debugging: $TEST_DIR"; fi' EXIT

main "$@"
