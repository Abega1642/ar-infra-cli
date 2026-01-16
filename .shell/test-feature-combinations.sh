#!/bin/bash

set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.shell/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=.shell/lib/feature-validator.sh
source "$SCRIPT_DIR/lib/feature-validator.sh"

readonly BASE_TEST_DIR="test-feature-combinations"
readonly GROUP="dev.razafindratelo"
readonly ARTIFACT="feature-test"
readonly VERSION="0.0.1"

declare -a FEATURE_COMBINATIONS=(
  # No features
  "no_features:--features=:"

  # Single database features
  "postgresql:--features=postgresql:postgresql"
  "mysql:--features=mysql:mysql"

  # Single non-database features
  "rabbitmq:--features=rabbitmq:rabbitmq"
  "s3_bucket:--features=s3_bucket:s3_bucket"
  "email:--features=email:email"

  # PostgreSQL combinations
  "postgresql_rabbitmq:--features=postgresql,rabbitmq:postgresql rabbitmq"
  "postgresql_s3_bucket:--features=postgresql,s3_bucket:postgresql s3_bucket"
  "postgresql_email:--features=postgresql,email:postgresql email"
  "postgresql_rabbitmq_s3_bucket:--features=postgresql,rabbitmq,s3_bucket:postgresql rabbitmq s3_bucket"
  "postgresql_rabbitmq_email:--features=postgresql,rabbitmq,email:postgresql rabbitmq email"
  "postgresql_s3_bucket_email:--features=postgresql,s3_bucket,email:postgresql s3_bucket email"
  "postgresql_all:--features=postgresql,rabbitmq,s3_bucket,email:postgresql rabbitmq s3_bucket email"

  # MySQL combinations
  "mysql_rabbitmq:--features=mysql,rabbitmq:mysql rabbitmq"
  "mysql_s3_bucket:--features=mysql,s3_bucket:mysql s3_bucket"
  "mysql_email:--features=mysql,email:mysql email"
  "mysql_rabbitmq_s3_bucket:--features=mysql,rabbitmq,s3_bucket:mysql rabbitmq s3_bucket"
  "mysql_rabbitmq_email:--features=mysql,rabbitmq,email:mysql rabbitmq email"
  "mysql_s3_bucket_email:--features=mysql,s3_bucket,email:mysql s3_bucket email"
  "mysql_all:--features=mysql,rabbitmq,s3_bucket,email:mysql rabbitmq s3_bucket email"

  # Non-database combinations
  "rabbitmq_s3_bucket:--features=rabbitmq,s3_bucket:rabbitmq s3_bucket"
  "rabbitmq_email:--features=rabbitmq,email:rabbitmq email"
  "s3_bucket_email:--features=s3_bucket,email:s3_bucket email"
  "rabbitmq_s3_bucket_email:--features=rabbitmq,s3_bucket,email:rabbitmq s3_bucket email"
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
  local enabled_features="${3:-}"

  local concatained_test_name="${test_name//,/_}"
  local test_dir="$BASE_TEST_DIR/$concatained_test_name"
  local project_dir="$test_dir/$ARTIFACT"

  print_info "+++++++++++++++++++++++++++++++++++++++++"
  print_info "Test: $test_name"
  print_info "Features: ${enabled_features:-none}"
  print_info "+++++++++++++++++++++++++++++++++++++++++"
  echo ""

  mkdir -p "$test_dir"
  cd "$test_dir" || return 1

  local cmd=(
    python -m src.ar_infra.cli.main init
    --group="$GROUP"
    --artifact="$ARTIFACT"
    --project-version="$VERSION"
    --path=./
    --project-dir="$ARTIFACT"
    --no-cache
    --skip-github-app
  )

  [ -n "$feature_flag" ] && cmd+=("$feature_flag")

  local python_path
  python_path="$(setup_python_path "$PROJECT_ROOT")"

  if ! PYTHONPATH="$python_path" "${cmd[@]}"; then
    print_error "Project generation failed"
    cd "$PROJECT_ROOT" || exit 1
    return 1
  fi

  print_success "Project generated"
  echo ""

  if is_windows; then
    wait_for_git_unlock "$project_dir" || true
  fi


  cd "$PROJECT_ROOT" || return 1

  local feature_array=()
  read -ra feature_array <<< "$enabled_features"

  local validation_errors
  if [ "${#feature_array[@]}" -eq 0 ]; then
    validation_errors="$(validate_features "$project_dir" "$GROUP" "$ARTIFACT")"
  else
    validation_errors="$(validate_features "$project_dir" "$GROUP" "$ARTIFACT" "${feature_array[@]}")"
  fi

  if [ "$validation_errors" -eq 0 ]; then
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
  local total_tests="${#FEATURE_COMBINATIONS[@]}"

  echo "+++++++++++++++++++++++++++++++++++++++++"
  echo "AR-INFRA Feature Combination Tests"
  echo "+++++++++++++++++++++++++++++++++++++++++"
  echo ""

  cleanup

  PROJECT_ROOT="$(get_project_root)" || exit 1
  mkdir -p "$BASE_TEST_DIR"

  for combination in "${FEATURE_COMBINATIONS[@]}"; do
    IFS=':' read -r test_name feature_flag enabled_features <<< "$combination"

    if run_single_test "$test_name" "$feature_flag" "$enabled_features"; then
      passed_tests=$((passed_tests + 1))
    else
      failed_tests=$((failed_tests + 1))
    fi

    echo ""
  done

  echo "+++++++++++++++++++++++++++++++++++++++++"
  echo "Test Summary"
  echo "+++++++++++++++++++++++++++++++++++++++++"
  print_info "Total:  $total_tests"
  print_success "Passed: $passed_tests"
  print_error "Failed: $failed_tests"
  echo ""

  if [ "$failed_tests" -eq 0 ]; then
    print_success "All feature combination tests passed!"
    cleanup
    exit 0
  else
    print_error "Some tests failed. Results kept in $BASE_TEST_DIR"
    exit 1
  fi
}

trap 'print_warning "Interrupted, cleaning up..."; cleanup' INT TERM
main "$@"
