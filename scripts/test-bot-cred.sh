#!/bin/bash

# test-bot-cred.sh - Integration test for bot credentials in compiled binaries.
# Tests that BOT_ID and BOT_SLUG secrets are correctly injected during build
# and that the generated project's initial commit is authored by the bot.

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

readonly TEST_DIR="test-bot-credentials"
readonly GROUP="dev.razafindratelo"
readonly ARTIFACT="bot-test"
readonly VERSION="0.0.1"
readonly PROJECT_DIR="bot-test"


if [ -z "${EXPECTED_BOT_ID:-}" ]; then
    print_error "EXPECTED_BOT_ID environment variable not set"
    print_info "This variable must be set by the CI workflow"
    exit 1
fi

if [ -z "${EXPECTED_BOT_SLUG:-}" ]; then
    print_error "EXPECTED_BOT_SLUG environment variable not set"
    print_info "This variable must be set by the CI workflow"
    exit 1
fi

readonly EXPECTED_BOT_NAME="${EXPECTED_BOT_SLUG}[bot]"
readonly EXPECTED_BOT_EMAIL="${EXPECTED_BOT_ID}+${EXPECTED_BOT_SLUG}[bot]@users.noreply.github.com"

print_info "Expected bot credentials:"
print_info "  Bot ID: ${EXPECTED_BOT_ID}"
print_info "  Bot Slug: ${EXPECTED_BOT_SLUG}"
print_info "  Bot Name: ${EXPECTED_BOT_NAME}"
print_info "  Bot Email: ${EXPECTED_BOT_EMAIL}"
echo ""

cleanup() {
    if [ -d "$TEST_DIR" ]; then
        print_info "Cleaning up test directory..."
        rm -rf "$TEST_DIR"
    fi
}

find_binary() {
    local binary_name=""
    local project_root="$1"

    if is_windows; then
        binary_name="ar-infra.exe"
    else
        binary_name="ar-infra"
    fi

    local search_paths=(
        "$project_root/dist/$binary_name"
        "$project_root/$binary_name"
        "$(which ar-infra 2>/dev/null || echo "")"
    )

    for path in "${search_paths[@]}"; do
        if [ -n "$path" ] && [ -f "$path" ]; then
            if [[ "$path" = /* ]]; then
                echo "$path"
            else
                echo "$(cd "$(dirname "$path")" && pwd)/$(basename "$path")"
            fi
            return 0
        fi
    done

    print_error "Binary not found. Searched paths: ${search_paths[*]}"
    return 1
}

run_project_generation() {
    local binary_path="$1"

    print_info "Running ar-infra init command with binary: $binary_path"

    local cmd=(
        "$binary_path" init
        --group="$GROUP"
        --artifact="$ARTIFACT"
        --project-version="$VERSION"
        --path=./
        --project-dir="$PROJECT_DIR"
        --feature=email
    )

    if "${cmd[@]}"; then
        print_success "CLI command executed successfully"
        return 0
    else
        print_error "CLI command failed"
        return 1
    fi
}

check_git_repository() {
    local project_path="$1"

    if [ ! -d "$project_path/.git" ]; then
        print_error "Git repository not initialized in $project_path"
        return 1
    fi

    print_success "Git repository exists"
    return 0
}

extract_commit_author() {
    local project_path="$1"

    if ! git -C "$project_path" rev-parse HEAD &>/dev/null; then
        print_error "No commits found in repository"
        return 1
    fi

    local author_name
    author_name=$(git -C "$project_path" log -1 --pretty=format:'%an')

    local author_email
    author_email=$(git -C "$project_path" log -1 --pretty=format:'%ae')

    local commit_message
    commit_message=$(git -C "$project_path" log -1 --pretty=format:'%s')

    echo "$author_name|$author_email|$commit_message"
}

validate_bot_identity() {
    local author_info="$1"

    IFS='|' read -r author_name author_email commit_message <<< "$author_info"

    print_info "Actual Commit Details:"
    print_info "  Author Name: $author_name"
    print_info "  Author Email: $author_email"
    print_info "  Commit Message: $commit_message"
    echo ""

    local errors=0

    if [ "$author_name" == "$EXPECTED_BOT_NAME" ]; then
        print_success "Author name matches expected: $EXPECTED_BOT_NAME"
    else
        print_error "Author name mismatch!"
        print_error "  Expected: $EXPECTED_BOT_NAME"
        print_error "  Got: $author_name"
        ((errors++))
    fi

    if [ "$author_email" == "$EXPECTED_BOT_EMAIL" ]; then
        print_success "Author email matches expected: $EXPECTED_BOT_EMAIL"
    else
        print_error "Author email mismatch!"
        print_error "  Expected: $EXPECTED_BOT_EMAIL"
        print_error "  Got: $author_email"
        ((errors++))
    fi

    if [[ "$author_email" =~ ^123456789\+ ]]; then
        print_error "CRITICAL: Using fallback BOT_ID (123456789)!"
        print_error "This means secrets were NOT injected during build"
        ((errors++))
    else
        print_success "Bot ID is NOT the fallback value - secrets were injected"
    fi

    if [[ "$commit_message" == "infra: generate the spring boot infrastructure" ]]; then
        print_success "Commit message matches expected format"
    else
        print_warning "Commit message differs from expected: $commit_message"
    fi

    return $errors
}

count_commits() {
    local project_path="$1"

    local commit_count
    commit_count=$(git -C "$project_path" rev-list --count HEAD)

    print_info "Total commits in repository: $commit_count"

    if [ "$commit_count" -eq 1 ]; then
        print_success "Repository has exactly one commit (as expected)"
        return 0
    else
        print_error "Expected 1 commit, found $commit_count"
        return 1
    fi
}

check_initial_branch() {
    local project_path="$1"

    local current_branch
    current_branch=$(git -C "$project_path" branch --show-current)

    print_info "Current branch: $current_branch"

    if [ "$current_branch" == "preprod" ]; then
        print_success "Initial branch is 'preprod' (as expected)"
        return 0
    else
        print_warning "Expected branch 'preprod', found '$current_branch'"
        return 1
    fi
}

display_full_commit_info() {
    local project_path="$1"

    print_info "Full commit information:"
    echo ""
    git -C "$project_path" log -1 --pretty=fuller || true
    echo ""
}

main() {
    local exit_code=0

    echo "********************************************"
    echo "AR-INFRA-CLI Bot Credentials Test"
    echo "********************************************"
    echo ""

    cleanup

    print_info "Creating test directory: $TEST_DIR"
    mkdir -p "$TEST_DIR"

    local project_root
    project_root=$(get_project_root) || exit 1

    print_info "Locating compiled binary..."
    local binary_path
    if ! binary_path=$(find_binary "$project_root"); then
        print_error "Could not locate ar-infra binary"
        print_info "Make sure the binary is built and available in ./dist/ or in PATH"
        exit 1
    fi

    if ! is_windows && [ -f "$binary_path" ]; then
        chmod +x "$binary_path" 2>/dev/null || true
    fi

    print_success "Binary found: $binary_path"
    echo ""

    cd "$TEST_DIR" || {
        print_error "Failed to change to test directory"
        exit 1
    }

    if ! run_project_generation "$binary_path"; then
        cd "$project_root" || exit 1
        print_error "Project generation failed"
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

    local project_path="$TEST_DIR/$PROJECT_DIR"

    if [ ! -d "$project_path" ]; then
        print_error "Project directory was not created!"
        exit 1
    fi
    print_success "Project directory created: $project_path"
    echo ""

    print_info "Validating Git repository..."
    if ! check_git_repository "$project_path"; then
        exit 1
    fi
    echo ""

    print_info "Checking commit count..."
    local commit_count_errors=0
    count_commits "$project_path" || commit_count_errors=$?
    echo ""

    print_info "Checking initial branch..."
    local branch_errors=0
    check_initial_branch "$project_path" || branch_errors=$?
    echo ""

    print_info "Extracting commit author information..."
    local author_info
    if ! author_info=$(extract_commit_author "$project_path"); then
        exit 1
    fi
    echo ""

    print_info "Validating bot identity..."
    local identity_errors=0
    validate_bot_identity "$author_info" || identity_errors=$?
    echo ""

    display_full_commit_info "$project_path"

    local total_errors=$((identity_errors + commit_count_errors + branch_errors))

    echo "********************************************"
    echo "Test Summary"
    echo "********************************************"

    if [ $total_errors -eq 0 ]; then
        print_success "All bot credential checks passed!"
        echo ""
        print_info "The binary correctly uses injected secrets:"
        print_info "Bot identity is properly configured"
        print_info "Commit author matches expected bot credentials"
        print_info "No fallback credentials detected"
        print_info "Expected Bot ID: ${EXPECTED_BOT_ID}"
        print_info "Expected Bot Slug: ${EXPECTED_BOT_SLUG}"
        echo ""
        print_info "Test directory preserved for inspection: $TEST_DIR"
        print_info "Run 'rm -rf $TEST_DIR' to clean up"
        exit_code=0
    else
        print_error "Bot credential test failed with $total_errors error(s)"
        echo ""
        print_info "Breakdown:"
        print_info "  Bot identity validation errors: $identity_errors"
        print_info "  Commit count errors: $commit_count_errors"
        print_info "  Branch validation errors: $branch_errors"
        echo ""

        if [ $identity_errors -gt 0 ]; then
            echo "---------------------------------------------"
            print_error "POSSIBLE CAUSES:"
            print_info "1. Test secrets (BOT_ID_TEST, BOT_SLUG_TEST) not set in GitHub repository"
            print_info "2. Secrets not injected during binary build (check ci-test-bot-cred.yml)"
            print_info "3. config.py still using os.getenv() instead of direct assignment"
            print_info "4. Binary was not built with test secrets"
            print_info "5. Mismatch between EXPECTED_BOT_ID/SLUG and actual secrets used"
            echo "---------------------------------------------"
            echo ""
            print_info "Expected credentials (from environment):"
            print_info "  BOT_ID: ${EXPECTED_BOT_ID}"
            print_info "  BOT_SLUG: ${EXPECTED_BOT_SLUG}"
        fi

        echo ""
        print_info "Test directory preserved for debugging: $TEST_DIR"
        exit_code=1
    fi

    exit $exit_code
}

trap 'if [ $? -ne 0 ]; then print_warning "Test directory preserved for debugging: $TEST_DIR"; fi' EXIT

main "$@"
