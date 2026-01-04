#!/bin/bash

# test-feature-combinations.sh - Test all feature combinations
# Generates projects with different feature sets and validates correctness

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=scripts/lib/feature-validator.sh
source "$SCRIPT_DIR/lib/feature-validator.sh"

readonly BASE_TEST_DIR="test-feature-combinations"
readonly GROUP="dev.razafindratelo"
readonly ARTIFACT="feature-test"
readonly VERSION="0.0.1"

# All possible feature combinations (15 total)
declare -a FEATURE_COMBINATIONS=(
    "no-features:--no-features:"
    "postgresql:--features=postgresql:postgresql"
    "rabbitmq:--features=rabbitmq:rabbitmq"
    "s3_bucket:--features=s3_bucket:s3_bucket"
    "email:--features=email:email"
    "postgresql,rabbitmq:--features=postgresql,rabbitmq:postgresql rabbitmq"
    "postgresql,s3_bucket:--features=postgresql,s3_bucket:postgresql s3_bucket"
    "postgresql,email:--features=postgresql,email:postgresql email"
    "rabbitmq,s3_bucket:--features=rabbitmq,s3_bucket:rabbitmq s3_bucket"
    "rabbitmq,email:--features=rabbitmq,email:rabbitmq email"
    "s3_bucket,email:--features=s3_bucket,email:s3_bucket email"
    "postgresql,rabbitmq,s3_bucket:--features=postgresql,rabbitmq,s3_bucket:postgresql rabbitmq s3_bucket"
    "postgresql,rabbitmq,email:--features=postgresql,rabbitmq,email:postgresql rabbitmq email"
    "postgresql,s3_bucket,email:--features=postgresql,s3_bucket,email:postgresql s3_bucket email"
    "rabbitmq,s3_bucket,email:--features=rabbitmq,s3_bucket,email:rabbitmq s3_bucket email"
)

cleanup() {
    if [ -d "$BASE_TEST_DIR" ]; then
        print_info "Cleaning up test directory..."
        rm -rf "$BASE_TEST_DIR"
    fi
}

run_single_test() {
    local test_name="$1"
    local feature_flag="$2"
    local enabled_features="$3"
    local project_dir="$BASE_TEST_DIR/$test_name/$ARTIFACT"

    print_info "++++++++++++++++++++++++++++++++++"
    print_info "Test: $test_name"
    print_info "Features: ${enabled_features:-none}"
    print_info "++++++++++++++++++++++++++++++++++"
    echo ""

    mkdir -p "$BASE_TEST_DIR/$test_name"
    cd "$BASE_TEST_DIR/$test_name" || return 1

    local cmd=(
        python -m src.ar_infra.cli.main init
        --group="$GROUP"
        --artifact="$ARTIFACT"
        --version="$VERSION"
        --path=./
        --project-dir="$ARTIFACT"
        --no-cache
    )

    # Add feature flag
    if [ -n "$feature_flag" ]; then
        cmd+=("$feature_flag")
    fi

    local python_path
    python_path=$(setup_python_path "$PROJECT_ROOT")

    if ! PYTHONPATH="$python_path" "${cmd[@]}" > /dev/null 2>&1; then
        print_error "Project generation failed"
        cd "$PROJECT_ROOT" || exit 1
        return 1
    fi

    print_success "Project generated"
    echo ""

    # Wait for Git on Windows
    if is_windows; then
        wait_for_git_unlock "$project_dir"
    fi

    # Return to project root
    cd "$PROJECT_ROOT" || return 1

    # Validate features
    local feature_array
    read -ra feature_array <<< "$enabled_features"

    local validation_errors=0
    validate_features "$project_dir" "$GROUP" "$ARTIFACT" "${feature_array[@]}" || validation_errors=$?

    if [ $validation_errors -eq 0 ]; then
        print_success "Feature validation passed"
        return 0
    else
        print_error "Feature validation failed with $validation_errors error(s)"
        return 1
    fi
}

main() {
    local failed_tests=0
    local passed_tests=0
    local total_tests=${#FEATURE_COMBINATIONS[@]}

    echo "++++++++++++++++++++++++++++++++++"
    echo "AR-INFRA Feature Combination Test Suite"
    echo "++++++++++++++++++++++++++++++++++"
    echo ""
    print_info "Total tests to run: $total_tests"
    echo ""

    cleanup

    PROJECT_ROOT=$(get_project_root) || exit 1
    print_info "Project root: $PROJECT_ROOT"
    echo ""

    mkdir -p "$BASE_TEST_DIR"

    local start_time
    start_time=$(date +%s)

    for combination in "${FEATURE_COMBINATIONS[@]}"; do
        IFS=':' read -r test_name feature_flag enabled_features <<< "$combination"

        if run_single_test "$test_name" "$feature_flag" "$enabled_features"; then
            ((passed_tests++))
        else
            ((failed_tests++))
        fi

        echo ""
        echo "++++++++++++++++++++++++++++++++++"
        echo ""
    done

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "++++++++++++++++++++++++++++++++++"
    echo "Test Summary"
    echo "++++++++++++++++++++++++++++++++++"
    print_info "Total tests: $total_tests"
    print_success "Passed: $passed_tests"

    if [ $failed_tests -gt 0 ]; then
        print_error "Failed: $failed_tests"
    else
        print_info "Failed: 0"
    fi

    print_info "Duration: ${duration}s"
    echo ""

    if [ $failed_tests -eq 0 ]; then
        print_success "All feature combination tests passed!"
        cleanup
        exit 0
    else
        print_error "Some tests failed. Test directory preserved: $BASE_TEST_DIR"
        exit 1
    fi
}

trap 'print_warning "Test interrupted. Cleaning up..."; cleanup' INT TERM

main "$@"
