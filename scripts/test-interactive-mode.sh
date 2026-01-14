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
  "no-db:n:::"
  "postgresql:y:postgresql::postgresql"
  "mysql:y:mysql::mysql"
  "postgresql-rabbitmq:y:postgresql:rabbitmq:postgresql rabbitmq"
  "postgresql-s3:y:postgresql:s3_bucket:postgresql s3_bucket"
  "postgresql-email:y:postgresql:email:postgresql email"
  "mysql-rabbitmq:y:mysql:rabbitmq:mysql rabbitmq"
  "mysql-s3:y:mysql:s3_bucket:mysql s3_bucket"
  "mysql-email:y:mysql:email:mysql email"
  "postgresql-rabbitmq-s3:y:postgresql:rabbitmq s3_bucket:postgresql rabbitmq s3_bucket"
  "postgresql-rabbitmq-email:y:postgresql:rabbitmq email:postgresql rabbitmq email"
  "postgresql-s3-email:y:postgresql:s3_bucket email:postgresql s3_bucket email"
  "mysql-rabbitmq-s3:y:mysql:rabbitmq s3_bucket:mysql rabbitmq s3_bucket"
  "mysql-rabbitmq-email:y:mysql:rabbitmq email:mysql rabbitmq email"
  "mysql-s3-email:y:mysql:s3_bucket email:mysql s3_bucket email"
  "postgresql-all:y:postgresql:rabbitmq s3_bucket email:postgresql rabbitmq s3_bucket email"
  "mysql-all:y:mysql:rabbitmq s3_bucket email:mysql rabbitmq s3_bucket email"
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
  local add_database="$5"
  local database_choice="$6"
  local other_features="$7"
  local output_file="$8"

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

def send_down_arrow(child, count=1):
    for _ in range(count):
        # Try different escape sequences for better compatibility
        try:
            child.send('\x1b[B')  # Standard ANSI down arrow
        except:
            try:
                child.send('\x1bOB')  # Alternative down arrow
            except:
                child.send('j')  # Fallback: some terminals use j for down
        time.sleep(0.3)  # Longer delay for CI environments

def send_up_arrow(child, count=1):
    for _ in range(count):
        try:
            child.send('\x1b[A')  # Standard ANSI up arrow
        except:
            try:
                child.send('\x1bOA')  # Alternative up arrow
            except:
                child.send('k')  # Fallback: some terminals use k for up
        time.sleep(0.3)  # Longer delay for CI environments

def main():
    group = sys.argv[1]
    artifact = sys.argv[2]
    version = sys.argv[3]
    dest_path = sys.argv[4]
    add_database = sys.argv[5] if len(sys.argv) > 5 else "n"
    database_choice = sys.argv[6] if len(sys.argv) > 6 else ""
    other_features = " ".join(sys.argv[7:]) if len(sys.argv) > 7 else ""

    print(f"DEBUG: Arguments received:", file=sys.stderr)
    print(f"  group={group}", file=sys.stderr)
    print(f"  artifact={artifact}", file=sys.stderr)
    print(f"  version={version}", file=sys.stderr)
    print(f"  add_database={add_database}", file=sys.stderr)
    print(f"  database_choice={database_choice}", file=sys.stderr)
    print(f"  other_features='{other_features}'", file=sys.stderr)

    if IS_WINDOWS:
        child = pexpect_spawn.PopenSpawn(
            f'python -m src.ar_infra.cli.main init --skip-github-app',
            encoding='utf-8',
            timeout=120
        )
    else:
        child = pexpect.spawn(
            'python',
            ['-m', 'src.ar_infra.cli.main', 'init', '--skip-github-app'],
            encoding='utf-8',
            timeout=120
        )

    child.logfile = sys.stdout

    try:
        child.expect('Press Enter to continue', timeout=30)
        child.sendline('')
        time.sleep(0.5)

        child.expect('Group ID:', timeout=30)
        time.sleep(0.5)
        child.send('\x15')  # Ctrl+U to clear line
        time.sleep(0.2)
        child.sendline(group)
        time.sleep(0.5)

        child.expect('Artifact ID', timeout=30)
        time.sleep(0.5)
        child.send('\x15')  # Ctrl+U to clear line
        time.sleep(0.2)
        child.sendline(artifact)
        time.sleep(0.5)

        child.expect('Version:', timeout=30)
        time.sleep(0.5)
        child.send('\x15')  # Ctrl+U to clear line
        time.sleep(0.2)
        child.sendline(version)
        time.sleep(0.5)

        child.expect('Destination Directory', timeout=30)
        time.sleep(0.5)
        child.send('\x15')  # Ctrl+U to clear line
        time.sleep(0.2)
        child.sendline(dest_path)
        time.sleep(0.5)

        child.expect('Project Directory Name', timeout=30)
        time.sleep(0.5)
        child.send('\x15')  # Ctrl+U to clear line
        time.sleep(0.2)
        child.sendline(artifact)
        time.sleep(0.5)

        child.expect('Would you like to add a database', timeout=30)
        time.sleep(0.5)
        child.sendline(add_database)
        time.sleep(0.5)

        if add_database.lower() not in ['n', 'no']:
            child.expect('Select database:', timeout=30)
            time.sleep(0.8)  # Extra wait for menu to render

            print(f"DEBUG: Selecting database: {database_choice}", file=sys.stderr)

            if database_choice and database_choice.lower() == 'mysql':
                print(f"DEBUG: Navigating to MySQL (down 1)", file=sys.stderr)
                send_down_arrow(child, 1)
                time.sleep(0.5)

            print(f"DEBUG: Confirming database selection", file=sys.stderr)
            child.sendline('')
            time.sleep(1.0)  # Extra wait for menu to clear

        child.expect('Select other features to Include:', timeout=30)
        time.sleep(0.8)  # Extra wait for menu to render

        print(f"DEBUG: Processing features: '{other_features}'", file=sys.stderr)

        if other_features and other_features.strip():
            feature_list = other_features.strip().split()
            print(f"DEBUG: Feature list: {feature_list}", file=sys.stderr)

            feature_map = {
                'rabbitmq': 0,
                's3_bucket': 1,
                'email': 2
            }

            for feature in feature_list:
                if feature in feature_map:
                    pos = feature_map[feature]
                    print(f"DEBUG: Selecting {feature} at position {pos}", file=sys.stderr)

                    send_down_arrow(child, pos)
                    time.sleep(0.3)

                    print(f"DEBUG: Pressing space to select {feature}", file=sys.stderr)
                    child.send(' ')
                    time.sleep(0.5)

                    send_up_arrow(child, pos)
                    time.sleep(0.3)


            print(f"DEBUG: Navigating to 'done' (down 3)", file=sys.stderr)
            send_down_arrow(child, 3)
            time.sleep(0.5)

        print(f"DEBUG: Confirming feature selection", file=sys.stderr)
        child.sendline('')
        time.sleep(1.0)

        child.expect('Use cached template', timeout=30)
        time.sleep(0.5)
        child.sendline('y')
        time.sleep(1.5)  # Extra wait for summary to render

        child.expect('Would you like to proceed', timeout=30)
        time.sleep(0.5)
        child.sendline('y')
        time.sleep(0.5)

        if IS_WINDOWS:
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

        # Properly close/terminate based on platform
        try:
            if IS_WINDOWS:
                if hasattr(child, 'terminate'):
                    child.terminate(force=True)
            else:
                child.close(force=True)
        except:
            pass

        return 1

if __name__ == '__main__':
    sys.exit(main())
EOF_PEXPECT

  chmod +x "$output_file"
}

run_single_test() {
  local test_name="$1"
  local add_database="$2"
  local database_choice="$3"
  local other_features_input="$4"
  local enabled_features="${5:-}"

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

  generate_pexpect_script "$GROUP" "$ARTIFACT" "$VERSION" "./" "$add_database" "$database_choice" "$other_features_input" "$pexpect_script"

  cd "$test_dir" || return 1

  if ! PYTHONPATH="$python_path" python "$pexpect_script" "$GROUP" "$ARTIFACT" "$VERSION" "./" "$add_database" "$database_choice" "$other_features_input"; then
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
    IFS=':' read -r test_name add_database database_choice other_features enabled_features <<< "$combination"

    if run_single_test "$test_name" "$add_database" "$database_choice" "$other_features" "$enabled_features"; then
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
