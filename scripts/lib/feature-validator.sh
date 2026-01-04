#!/bin/bash
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${_COMMON_SH_LOADED:-}" ]; then
  # shellcheck source=scripts/lib/common.sh
  source "$SCRIPT_DIR/common.sh"
fi


package_to_path() {
  echo "${1//.//}/${2//-/_}"
}


path_exists() {
  local project="$1"
  local type="$2"
  local path="$3"

  case "$type" in
    file) [ -f "$project/$path" ] ;;
    directory) [ -d "$project/$path" ] ;;
    *) return 1 ;;
  esac
}


build_postgresql_files() {
  local p="$1"
  POSTGRESQL_FILES=(
    "directory:src/main/java/$p/repository"
    "directory:src/main/resources/db"
    "file:src/main/java/$p/endpoint/rest/controller/health/HealthRepositoryController.java"
    "file:src/main/java/$p/service/health/HealthRepositoryService.java"
    "file:src/test/java/$p/conf/PostgresConf.java"
    "file:src/test/java/$p/endpoint/rest/controller/health/HealthRepositoryControllerIT.java"
  )
}

build_rabbitmq_files() {
  local p="$1"
  RABBITMQ_FILES=(
    "directory:src/main/java/$p/event"
    "directory:src/main/java/$p/datastructure"
    "file:src/main/java/$p/config/RabbitConfig.java"
    "file:src/main/java/$p/service/health/HealthEventService.java"
    "file:src/main/java/$p/endpoint/rest/controller/health/HealthEventController.java"
    "file:src/test/java/$p/conf/RabbitMQConf.java"
  )
}

build_s3_bucket_files() {
  local p="$1"
  S3_BUCKET_FILES=(
    "directory:src/main/java/$p/exception/bucket"
    "file:src/main/java/$p/config/BucketConf.java"
    "file:src/main/java/$p/file/BucketComponent.java"
    "file:src/main/java/$p/service/health/HealthBucketService.java"
  )
}

build_email_files() {
  local p="$1"
  EMAIL_FILES=(
    "directory:src/main/java/$p/mail"
    "file:src/main/java/$p/config/EmailConf.java"
    "file:src/main/java/$p/service/health/HealthEmailService.java"
  )
}


validate_present() {
  local project="$1" label="$2"
  shift 2
  local errors=0

  echo "[INFO] Checking presence of $label" >&2

  for entry in "$@"; do
    local type="${entry%%:*}"
    local path="${entry#*:}"
    if path_exists "$project" "$type" "$path"; then
      echo "[OK] $label: $path" >&2
    else
      echo "[ERR] $label missing: $path" >&2
      ((errors++))
    fi
  done

  echo "$errors"
}

validate_absent() {
  local project="$1" label="$2"
  shift 2
  local errors=0

  echo "[INFO] Checking absence of $label" >&2

  for entry in "$@"; do
    local path="${entry#*:}"
    if [ -e "$project/$path" ]; then
      echo "[ERR] $label should NOT exist: $path" >&2
      ((errors++))
    else
      echo "[OK] $label absent: $path" >&2
    fi
  done

  echo "$errors"
}

validate_features() {
  local project="$1" group="$2" artifact="$3"
  shift 3
  local enabled=("$@")
  local total_errors=0

  local pkg
  pkg="$(package_to_path "$group" "$artifact")"

  build_postgresql_files "$pkg"
  build_rabbitmq_files "$pkg"
  build_s3_bucket_files "$pkg"
  build_email_files "$pkg"

  for feature in postgresql rabbitmq s3_bucket email; do
    local on=false
    for e in "${enabled[@]}"; do
      [ "$e" = "$feature" ] && on=true
    done

    local err=0
    case "$feature" in
      postgresql)
        err="$($on && validate_present "$project" PostgreSQL "${POSTGRESQL_FILES[@]}" \
                 || validate_absent "$project" PostgreSQL "${POSTGRESQL_FILES[@]}")"
        ;;
      rabbitmq)
        err="$($on && validate_present "$project" RabbitMQ "${RABBITMQ_FILES[@]}" \
                 || validate_absent "$project" RabbitMQ "${RABBITMQ_FILES[@]}")"
        ;;
      s3_bucket)
        err="$($on && validate_present "$project" S3_BUCKET "${S3_BUCKET_FILES[@]}" \
                 || validate_absent "$project" S3_BUCKET "${S3_BUCKET_FILES[@]}")"
        ;;
      email)
        err="$($on && validate_present "$project" EMAIL "${EMAIL_FILES[@]}" \
                 || validate_absent "$project" EMAIL "${EMAIL_FILES[@]}")"
        ;;
    esac

    total_errors=$((total_errors + err))
  done

  echo "$total_errors"
}
