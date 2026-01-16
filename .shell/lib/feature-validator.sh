#!/bin/bash
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${_COMMON_SH_LOADED:-}" ]; then
  # shellcheck source=.shell/lib/common.sh
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

build_database_files() {
  local p="$1"
  # PostgreSQL and MySQL share the same files/directories
  DATABASE_FILES=(
    "directory:src/main/java/$p/repository"
    "directory:src/main/resources/db"
    "directory:src/test/java/$p/conf/db"
    "file:src/main/java/$p/endpoint/rest/controller/health/HealthRepositoryController.java"
    "file:src/main/java/$p/service/health/HealthRepositoryService.java"
    "file:src/test/java/$p/endpoint/rest/controller/health/HealthRepositoryControllerIT.java"
  )
}

build_rabbitmq_files() {
  local p="$1"
  RABBITMQ_FILES=(
    "directory:src/main/java/$p/event"
    "directory:src/main/java/$p/datastructure"
    "file:src/main/java/$p/config/RabbitConfig.java"
    "file:src/main/java/$p/datastructure/ListGrouper.java"
    "file:src/main/java/$p/service/health/HealthEventService.java"
    "file:src/main/java/$p/endpoint/rest/controller/health/HealthEventController.java"
    "file:src/test/java/$p/conf/RabbitMQConf.java"
    "file:src/test/java/$p/service/health/HealthEventServiceIT.java"
    "file:src/test/java/$p/endpoint/rest/controller/health/HealthEventControllerIT.java"
  )
}

build_s3_bucket_files() {
  local p="$1"
  S3_BUCKET_FILES=(
    "directory:src/main/java/$p/exception/bucket"
    "file:src/main/java/$p/config/BucketConf.java"
    "file:src/main/java/$p/file/BucketComponent.java"
    "file:src/main/java/$p/endpoint/rest/controller/health/HealthBucketController.java"
    "file:src/main/java/$p/service/health/HealthBucketService.java"
    "file:src/test/java/$p/conf/BucketConf.java"
    "file:src/test/java/$p/file/BucketComponentIT.java"
    "file:src/test/java/$p/service/health/HealthBucketServiceIT.java"
    "file:src/test/java/$p/endpoint/rest/controller/health/HealthBucketControllerIT.java"
  )
}

build_email_files() {
  local p="$1"
  EMAIL_FILES=(
    "directory:src/main/java/$p/mail"
    "directory:src/test/java/$p/mail"
    "file:src/main/java/$p/config/EmailConf.java"
    "file:src/main/java/$p/service/health/HealthEmailService.java"
    "file:src/main/java/$p/exception/EmailSendException.java"
    "file:src/main/java/$p/exception/health/EmailHealthCheckException.java"
    "file:src/main/java/$p/endpoint/rest/controller/health/HealthEmailController.java"
    "file:src/test/java/$p/conf/EmailConf.java"
    "file:src/test/java/$p/service/health/HealthEmailServiceIT.java"
    "file:src/test/java/$p/endpoint/rest/controller/health/HealthEmailControllerIT.java"
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

has_database_feature() {
  if [ $# -eq 0 ]; then
    return 1
  fi

  for e in "$@"; do
    if [ "$e" = "postgresql" ] || [ "$e" = "mysql" ]; then
      return 0
    fi
  done
  return 1
}

validate_features() {
  local project="$1" group="$2" artifact="$3"
  shift 3
  local enabled=("$@")
  local total_errors=0

  local pkg
  pkg="$(package_to_path "$group" "$artifact")"

  build_database_files "$pkg"
  build_rabbitmq_files "$pkg"
  build_s3_bucket_files "$pkg"
  build_email_files "$pkg"

  # Check database features (PostgreSQL and MySQL share the same files)
  local database_enabled=false
  if [ "${#enabled[@]}" -gt 0 ] && has_database_feature "${enabled[@]}"; then
    database_enabled=true
  fi

  local err
  if [ "$database_enabled" = true ]; then
    err="$(validate_present "$project" "Database" "${DATABASE_FILES[@]}")"
  else
    err="$(validate_absent "$project" "Database" "${DATABASE_FILES[@]}")"
  fi
  err="${err:-0}"
  total_errors=$((total_errors + err))

  for feature in rabbitmq s3_bucket email; do
    local on=false

    if [ "${#enabled[@]}" -gt 0 ]; then
      for e in "${enabled[@]}"; do
        [ "$e" = "$feature" ] && on=true
      done
    fi

    local err
    if [ "$on" = true ]; then
      case "$feature" in
      rabbitmq)
        err="$(validate_present "$project" RabbitMQ "${RABBITMQ_FILES[@]}")"
        ;;
      s3_bucket)
        err="$(validate_present "$project" S3_BUCKET "${S3_BUCKET_FILES[@]}")"
        ;;
      email)
        err="$(validate_present "$project" EMAIL "${EMAIL_FILES[@]}")"
        ;;
      esac
    else
      case "$feature" in
      rabbitmq)
        err="$(validate_absent "$project" RabbitMQ "${RABBITMQ_FILES[@]}")"
        ;;
      s3_bucket)
        err="$(validate_absent "$project" S3_BUCKET "${S3_BUCKET_FILES[@]}")"
        ;;
      email)
        err="$(validate_absent "$project" EMAIL "${EMAIL_FILES[@]}")"
        ;;
      esac
    fi

    err="${err:-0}"
    total_errors=$((total_errors + err))
  done

  echo "$total_errors"
}
