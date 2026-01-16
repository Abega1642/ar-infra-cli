#!/bin/bash

# add-dependency.sh - Integration test for ar-infra-cli add-dependency command.
# Tests the 'add-dependency' command and validates dependency additions to build.gradle.

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.shell/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

readonly TEST_DIR="test-add-dependency"
readonly GROUP="dev.razafindratelo"
readonly ARTIFACT="demo"
readonly VERSION="0.0.1"
readonly PROJECT_DIR="demo"
readonly BUILD_GRADLE="$TEST_DIR/$PROJECT_DIR/build.gradle"

readonly SINGLE_DEP="implementation 'org.springframework.boot:spring-boot-starter-data-jpa'"
readonly MULTI_DEPS=(
  "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'"
  "runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'"
  "runtimeOnly 'io.jsonwebtoken:jjwt-jackson:0.13.0'"
)

cleanup() {
  if [ -d "$TEST_DIR" ]; then
    print_info "Cleaning up test directory..."
    rm -rf "$TEST_DIR"
  fi
}

run_project_generation() {
  local project_root="$1"

  print_info "Running ar-infra-cli init command..."

  local python_path
  python_path=$(setup_python_path "$project_root")

  local cmd=(
    python -m src.ar_infra.cli.main init
    --group="$GROUP"
    --artifact="$ARTIFACT"
    --project-version="$VERSION"
    --path=./
    --project-dir="$PROJECT_DIR"
    --no-cache
    --skip-github-app
  )

  if PYTHONPATH="$python_path" "${cmd[@]}"; then
    print_success "Project generated successfully"
    return 0
  else
    print_error "Project generation failed"
    return 1
  fi
}

run_add_dependency() {
  local project_root="$1"
  local project_path="$2"
  shift 2
  local dependencies=("$@")

  print_info "Running ar-infra add-dependency command..."
  print_info "Adding ${#dependencies[@]} dependency(ies)"

  local python_path
  python_path=$(setup_python_path "$project_root")

  local cmd=(
    python -m src.ar_infra.cli.main add-dependency
    --project-path="$project_path"
  )

  for dep in "${dependencies[@]}"; do
    cmd+=("$dep")
  done

  if PYTHONPATH="$python_path" "${cmd[@]}"; then
    print_success "add-dependency command executed successfully"
    return 0
  else
    print_error "add-dependency command failed"
    return 1
  fi
}

check_dependency_in_build_gradle() {
  local dep_notation="$1"
  local config_type="${dep_notation%% *}" # Extract configuration (implementation, runtimeOnly, etc.)
  local dep_coords="${dep_notation#* }"   # Extract coordinates after configuration

  dep_coords="${dep_coords//\'/}"

  local group_artifact
  group_artifact=$(echo "$dep_coords" | cut -d: -f1,2)

  if grep -q "$group_artifact" "$BUILD_GRADLE"; then
    print_success "Dependency found in build.gradle: $group_artifact"
    return 0
  else
    print_error "Dependency NOT found in build.gradle: $group_artifact"
    return 1
  fi
}

validate_single_dependency() {
  print_info "Validating single dependency addition..."
  echo ""

  if check_dependency_in_build_gradle "$SINGLE_DEP"; then
    return 0
  else
    return 1
  fi
}

validate_multiple_dependencies() {
  print_info "Validating multiple dependencies addition..."
  echo ""

  local errors=0
  for dep in "${MULTI_DEPS[@]}"; do
    if ! check_dependency_in_build_gradle "$dep"; then
      ((errors++))
    fi
  done

  return $errors
}

display_build_gradle_content() {
  print_info "Current build.gradle content:"
  echo ""
  echo "----------------------------------------"
  cat "$BUILD_GRADLE"
  echo "----------------------------------------"
  echo ""
}

main() {
  local exit_code=0

  echo "********************************************"
  echo "AR-INFRA-CLI Add Dependency Test"
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

  print_info "Step 1: Generating project..."
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

  if [ ! -f "$BUILD_GRADLE" ]; then
    print_error "build.gradle not found at expected location!"
    exit 1
  fi
  print_success "Project generated and build.gradle found"
  echo ""

  print_info "Step 2: Adding single dependency..."
  local project_path="$TEST_DIR/$PROJECT_DIR"
  if ! run_add_dependency "$project_root" "$project_path" "$SINGLE_DEP"; then
    print_error "Failed to add single dependency"
    exit_code=1
  fi
  echo ""

  display_build_gradle_content

  local single_dep_errors=0
  validate_single_dependency || single_dep_errors=$?
  echo ""

  print_info "Step 3: Adding multiple dependencies..."
  if ! run_add_dependency "$project_root" "$project_path" "${MULTI_DEPS[@]}"; then
    print_error "Failed to add multiple dependencies"
    exit_code=1
  fi
  echo ""

  display_build_gradle_content

  local multi_dep_errors=0
  validate_multiple_dependencies || multi_dep_errors=$?
  echo ""

  local total_errors=$((single_dep_errors + multi_dep_errors))

  echo "********************************************"
  echo "Test Summary"
  echo "********************************************"

  if [ $exit_code -eq 0 ] && [ $total_errors -eq 0 ]; then
    print_success "All checks passed!"
    echo ""
    print_info "Successfully added:"
    print_info "  - 1 single dependency"
    print_info "  - ${#MULTI_DEPS[@]} multiple dependencies"
    echo ""
    print_info "Test directory preserved for inspection: $TEST_DIR"
    print_info "Run 'rm -rf $TEST_DIR' to clean up"
    exit_code=0
  else
    print_error "Test failed with $total_errors validation error(s)"
    echo ""
    print_info "Breakdown:"
    print_info "  Single dependency validation errors: $single_dep_errors"
    print_info "  Multiple dependencies validation errors: $multi_dep_errors"
    echo ""
    print_info "Test directory preserved for debugging: $TEST_DIR"
    exit_code=1
  fi

  exit $exit_code
}

trap 'if [ $? -ne 0 ]; then print_warning "Test directory preserved for debugging: $TEST_DIR"; fi' EXIT

main "$@"
