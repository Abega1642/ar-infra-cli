#!/usr/bin/env bash

set -euo pipefail


GREEN="\033[0;32m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"


PASSED=0
FAILED=0


log_test() {
  echo -e "${BLUE}[TEST]${RESET} $1"
}

log_pass() {
  echo -e "${GREEN}  PASSED${RESET}"
}

log_fail() {
  echo -e "${RED}  FAILED${RESET}"
}


run_check() {
  local name="$1"
  local cmd="$2"

  log_test "$name"

  if eval "$cmd"; then
    log_pass
    PASSED=$((PASSED + 1))
    return 0
  else
    log_fail
    FAILED=$((FAILED + 1))
    return 1
  fi
}


echo "================================================"
echo "  AR-INFRA Banner Verification"
echo "================================================"
echo


run_check "Banner file exists" \
  "[ -f src/ar_infra/cli/resources/banner.txt ]"

run_check "Banner file is not empty" \
  "[ -s src/ar_infra/cli/resources/banner.txt ]"

run_check "Banner contains ANSI escape codes" \
  "grep -q \$'\\x1b\\[' src/ar_infra/cli/resources/banner.txt"

run_check "Banner contains ANSI color sequences" \
  "grep -q '38;5;' src/ar_infra/cli/resources/banner.txt"

run_check "Banner contains block characters" \
  "grep -q '█' src/ar_infra/cli/resources/banner.txt"

run_check "Banner file size is within expected range (500–2000 bytes)" \
  "bash -c 'SIZE=\$(wc -c < src/ar_infra/cli/resources/banner.txt); [ \"\$SIZE\" -gt 500 ] && [ \"\$SIZE\" -lt 2000 ]'"


run_check "Python can import Banner class" \
  "python3 -c 'from src.ar_infra.cli.ui.banner import Banner'"

run_check "Banner loads successfully in Python" \
  "python3 -c 'from src.ar_infra.cli.ui.banner import Banner; data = Banner._load_banner(); assert len(data) > 100'"

run_check "Banner retains ANSI codes in Python" \
  "python3 -c 'from src.ar_infra.cli.ui.banner import Banner; data = Banner._load_banner(); assert \"\\x1b[\" in data'"


echo
echo "================================================"
echo "  Results"
echo "================================================"
echo -e "${GREEN}Passed: ${PASSED}${RESET}"
echo -e "${RED}Failed: ${FAILED}${RESET}"
echo


if [ "$FAILED" -eq 0 ]; then
  echo -e "${GREEN}All banner verification tests passed!${RESET}"
  echo
  echo "Banner preview:"
  echo "------------------------------------------------"
  cat src/ar_infra/cli/resources/banner.txt
  echo "------------------------------------------------"
  exit 0
else
  echo -e "${RED}Some banner verification tests failed.${RESET}"
  echo
  echo "Debug info:"
  wc -c src/ar_infra/cli/resources/banner.txt
  exit 1
fi
