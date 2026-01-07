#!/bin/bash

set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=scripts/lib/feature-validator.sh
source "$SCRIPT_DIR/lib/feature-validator.sh"

readonly BASE_TEST_DIR="test-interactive-mode"
readonly GROUP="dev.razafindratelo"
readonly ARTIFACT="interactive-test"
readonly VERSION="0.0.1"

declare -a FEATURE_COMBINATIONS=(
  "postgresql:postgresql:postgresql"
  "rabbitmq:rabbitmq:rabbitmq"
  "s3_bucket:s3_bucket:s3_bucket"
  "email:email:email"
  "postgresql,rabbitmq:postgresql rabbitmq:postgresql rabbitmq"
  "postgresql,s3_bucket:postgresql s3_bucket:postgresql s3_bucket"
  "postgresql,email:postgresql email:postgresql email"
  "rabbitmq,s3_bucket:rabbitmq s3_bucket:rabbitmq s3_bucket"
  "rabbitmq,email:rabbitmq email:rabbitmq email"
  "s3_bucket,email:s3_bucket email:s3_bucket email"
  "postgresql,rabbitmq,s3_bucket:postgresql rabbitmq s3_bucket:postgresql rabbitmq s3_bucket"
  "postgresql,rabbitmq,email:postgresql rabbitmq email:postgresql rabbitmq email"
  "postgresql,s3_bucket,email:postgresql s3_bucket email:postgresql s3_bucket email"
  "rabbitmq,s3_bucket,email:rabbitmq s3_bucket email:rabbitmq s3_bucket email"
)

check_pexpect_installed() {
  local python_path="$1"
  if ! PYTHONPATH="$python_path" python -c "import pexpect" 2>/dev/null; then
    print_error "The Python 'pexpect' module is required but not installed"
    print_info "Install it with: pip install pexpect"
    return 1
  fi
  return 0
}

cleanup() {
  if [ -d "$BASE_TEST_DIR" ]; then
    print_info "Cleaning up test directory..."
    rm -rf "$BASE_TEST_DIR"
  fi
}

generate_pexpect_script() {
  local group="$1"
  local artifact="$2"
  local version="$3"
  local dest_path="$4"
  local features="$5"
  local output_file="$6"

  cat > "$output_file" << 'EOF_PEXPECT'
#!/usr/bin/env python
import sys
import os
import time

IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    import pexpect.popen_spawn as pexpect_spawn
else:
    import pexpect

def main():
    group = sys.argv[1]
    artifact = sys.argv[2]
    version = sys.argv[3]
    dest_path = sys.argv[4]
    features = sys.argv[5] if len(sys.argv) > 5 else ""

    # Use popen_spawn on Windows, regular spawn on Unix
    if IS_WINDOWS:
        child = pexpect_spawn.PopenSpawn(
            f'python -m src.ar_infra.cli.main init',
            encoding='utf-8',
            timeout=120
        )
    else:
        child = pexpect.spawn(
            'python',
            ['-m', 'src.ar_infra.cli.main', 'init'],
            encoding='utf-8',
            timeout=120
        )

    child.logfile = sys.stdout

    try:
        # Wait for initial prompt and press Enter
        child.expect('Press Enter to continue', timeout=30)
        child.sendline('')
        time.sleep(0.5)

        # Group ID - Clear default "com.example" (11 chars)
        child.expect('Group ID:', timeout=30)
        time.sleep(0.3)
        for _ in range(20):  # Send enough backspaces to clear any default
            child.send('\x7f')  # Backspace
            time.sleep(0.05)
        child.sendline(group)
        time.sleep(0.5)

        # Artifact ID - Clear default "my-app" (6 chars)
        child.expect('Artifact ID', timeout=30)
        time.sleep(0.3)
        for _ in range(20):  # Send enough backspaces to clear any default
            child.send('\x7f')  # Backspace
            time.sleep(0.05)
        child.sendline(artifact)
        time.sleep(0.5)

        # Version - Clear default "1.0.0" (5 chars)
        child.expect('Version:', timeout=30)
        time.sleep(0.3)
        for _ in range(20):  # Send enough backspaces to clear any default
            child.send('\x7f')  # Backspace
            time.sleep(0.05)
        child.sendline(version)
        time.sleep(0.5)

        child.expect('Destination Directory', timeout=30)
        time.sleep(0.3)
        for _ in range(20):  # Send enough backspaces to clear any default
            child.send('\x7f')  # Backspace
            time.sleep(0.05)
        child.sendline(dest_path)
        time.sleep(0.5)

        child.expect('Project Directory Name', timeout=30)
        time.sleep(0.3)
        for _ in range(20):  # Send enough backspaces to clear any default
            child.send('\x7f')  # Backspace
            time.sleep(0.05)
        child.sendline(artifact)
        time.sleep(0.5)

        child.expect('Select Features to Include:', timeout=30)
        time.sleep(0.5)

        if features:
            # Parse features: "postgresql rabbitmq" -> ["postgresql", "rabbitmq"]
            feature_list = features.strip().split()

            feature_map = {
                'postgresql': 0,
                'rabbitmq': 1,
                's3_bucket': 2,
                'email': 3
            }

            for feature in feature_list:
                if feature in feature_map:
                    pos = feature_map[feature]

                    for _ in range(pos):
                        child.send('\x1b[B')  # Down arrow key
                        time.sleep(0.2)

                    child.send(' ')
                    time.sleep(0.3)

                    for _ in range(pos):
                        child.send('\x1b[A')  # Up arrow key
                        time.sleep(0.2)

        time.sleep(0.3)
        child.sendline('')
        time.sleep(0.5)

        child.expect('Use cached template', timeout=30)
        time.sleep(0.3)
        child.sendline('n')
        time.sleep(0.5)

        child.expect('Would you like to proceed', timeout=30)
        time.sleep(0.3)
        child.sendline('y')

        if IS_WINDOWS:
            # On Windows, just wait a bit for completion
            time.sleep(10)
            child.close()
        else:
            child.expect(pexpect.EOF, timeout=300)
            child.close()

        return child.exitstatus if child.exitstatus is not None else 0

    except Exception as e:
        error_type = type(e).__name__
        print(f"\nERROR: {error_type}: {e}", file=sys.stderr)

        if hasattr(child, 'before'):
            print(f"\nLast output:\n{child.before}", file=sys.stderr)

        child.close(force=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
EOF_PEXPECT

  chmod +x "$output_file"
}

run_single_test() {
  local test_name="$1"
  local feature_input="$2"
  local enabled_features="${3:-}"

  local test_dir="$BASE_TEST_DIR/$test_name"
  local project_dir="$test_dir/$ARTIFACT"
  local pexpect_script="$PROJECT_ROOT/$test_dir/run-test.py"

  print_info "+++++++++++++++++++++++++++++++++++++++++"
  print_info "Test: $test_name"
  print_info "Features: ${enabled_features:-none}"
  print_info "+++++++++++++++++++++++++++++++++++++++++"
  echo ""

  mkdir -p "$test_dir"

  local python_path
  python_path="$(setup_python_path "$PROJECT_ROOT")"

  generate_pexpect_script "$GROUP" "$ARTIFACT" "$VERSION" "./" "$feature_input" "$pexpect_script"

  cd "$test_dir" || return 1

  if ! PYTHONPATH="$python_path" python "$pexpect_script" "$GROUP" "$ARTIFACT" "$VERSION" "./" "$feature_input"; then
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
  validation_errors="$(validate_features "$project_dir" "$GROUP" "$ARTIFACT" "${feature_array[@]}")"

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
  echo "AR-INFRA Interactive Mode Tests"
  echo "+++++++++++++++++++++++++++++++++++++++++"
  echo ""

  PROJECT_ROOT="$(get_project_root)" || exit 1

  local python_path
  python_path="$(setup_python_path "$PROJECT_ROOT")"

  if ! check_pexpect_installed "$python_path"; then
    print_info "Attempting to install pexpect..."
    if pip install pexpect; then
      print_success "pexpect installed successfully"
    else
      print_error "Failed to install pexpect"
      exit 1
    fi
  fi

  cleanup
  mkdir -p "$BASE_TEST_DIR"

  for combination in "${FEATURE_COMBINATIONS[@]}"; do
    IFS=':' read -r test_name feature_input enabled_features <<< "$combination"

    if run_single_test "$test_name" "$feature_input" "$enabled_features"; then
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
    print_success "All interactive mode tests passed!"
    cleanup
    exit 0
  else
    print_error "Some tests failed. Results kept in $BASE_TEST_DIR"
    exit 1
  fi
}

trap 'print_warning "Interrupted, cleaning up..."; cleanup' INT TERM
main "$@"
