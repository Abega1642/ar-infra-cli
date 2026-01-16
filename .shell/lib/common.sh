#!/bin/bash

# common.sh - Common utilities for test .shell
# Provides cross-platform functionality for colors, validation, and error handling

# Prevent re-sourcing
if [ -n "${_COMMON_SH_LOADED:-}" ]; then
    return 0
fi
readonly _COMMON_SH_LOADED=1

set -e
set -u
set -o pipefail

if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi
readonly RED GREEN YELLOW BLUE NC

print_success() {
    printf "${GREEN}[PASS]${NC} %s\n" "$1"
}

print_error() {
    printf "${RED}[FAIL]${NC} %s\n" "$1"
}

print_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

print_warning() {
    printf "${YELLOW}[WARN]${NC} %s\n" "$1"
}

# Path validation to prevent OWASP path traversal attacks
# Reference: OWASP Path Traversal (CWE-22)
validate_path() {
    local path="$1"
    local base_dir="$2"

    # Convert to absolute path for comparison
    local abs_base
    abs_base=$(cd "$base_dir" 2>/dev/null && pwd) || {
        print_error "Base directory does not exist: $base_dir"
        return 1
    }

    local abs_path
    if [[ "$path" = /* ]]; then
        abs_path="$path"
    else
        abs_path="$abs_base/$path"
    fi

    # Normalize the path (remove .., ., etc)
    abs_path=$(readlink -f "$abs_path" 2>/dev/null || realpath -s "$abs_path" 2>/dev/null || echo "$abs_path")

    case "$abs_path" in
        "$abs_base"*)
            return 0
            ;;
        *)
            print_error "Security: Path traversal detected: $path"
            return 1
            ;;
    esac
}

get_project_root() {
    local script_dir
    # Get directory where common.sh is located (.shell/lib/)
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # Go up two levels: .shell/lib/ -> .shell/ -> project_root/
    local project_root
    project_root="$(cd "$script_dir/../.." && pwd)"

    case "$project_root" in
        /*) ;;
        *)
            print_error "Security: Project root must be an absolute path"
            return 1
            ;;
    esac

    echo "$project_root"
}

# Setup Python path for cross-platform execution
# Handles Windows (MSYS/Cygwin/Git Bash) vs Unix-like systems
setup_python_path() {
    local project_root="$1"
    local python_path

    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows: Use semicolon separator and convert paths if needed
        if command -v cygpath &> /dev/null; then
            python_path="$(cygpath -w "$project_root");"
        else
            # Fallback conversion for Git Bash on Windows
            python_path=$(echo "$project_root" | sed -e 's|^/\([a-z]\)/|\U\1:/|' -e 's|/|\\|g')
            python_path="${python_path};"
        fi
        export PYTHONIOENCODING=utf-8
    else
        # Unix-like: Use colon separator
        python_path="$project_root:"
    fi

    echo "$python_path"
}

# Wait for Git operations to complete (Windows-specific issue)
wait_for_git_unlock() {
    local project_path="$1"
    local max_attempts=10
    local attempt=1

    print_info "Waiting for Git operations to complete..."

    while [ $attempt -le $max_attempts ]; do
        if git -C "$project_path" status &>/dev/null; then
            print_success "Git repository is accessible"
            return 0
        fi

        print_info "Attempt $attempt/$max_attempts: Git still locked, waiting..."
        sleep 2
        ((attempt++))
    done

    print_warning "Git repository may still be locked after $max_attempts attempts"
    return 0
}

is_windows() {
    [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]
}

export -f print_success
export -f print_error
export -f print_info
export -f print_warning
export -f validate_path
export -f get_project_root
export -f setup_python_path
export -f wait_for_git_unlock
export -f is_windows
