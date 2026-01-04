#!/bin/bash

# feature-validator.sh - Feature-specific file and directory validation
# Validates that generated projects contain only files for selected features

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Only source common.sh if it hasn't been loaded yet
if [ -z "${_COMMON_SH_LOADED:-}" ]; then
    # shellcheck source=scripts/lib/common.sh
    source "$SCRIPT_DIR/common.sh"
fi

# Convert package name to path (e.g., "com.example.app" -> "com/example/app")
package_to_path() {
    local group="$1"
    local artifact="$2"
    echo "${group//.//}/${artifact//-/_}"
}

# Build feature file mappings dynamically based on actual package structure
build_postgresql_files() {
    local pkg_path="$1"
    declare -gA POSTGRESQL_FILES=(
        ["src/main/java/$pkg_path/repository"]="directory"
        ["src/main/resources/db"]="directory"
        ["src/test/java/$pkg_path/service/health"]="directory"
        ["src/main/java/$pkg_path/endpoint/rest/controller/health/HealthRepositoryController.java"]="file"
        ["src/main/java/$pkg_path/service/health/HealthRepositoryService.java"]="file"
        ["src/test/java/$pkg_path/conf/PostgresConf.java"]="file"
        ["src/test/java/$pkg_path/endpoint/rest/controller/health/HealthRepositoryControllerIT.java"]="file"
    )
}

build_rabbitmq_files() {
    local pkg_path="$1"
    declare -gA RABBITMQ_FILES=(
        ["src/main/java/$pkg_path/event"]="directory"
        ["src/main/java/$pkg_path/datastructure"]="directory"
        ["src/main/java/$pkg_path/config/RabbitConfig.java"]="file"
        ["src/main/java/$pkg_path/datastructure/ListGrouper.java"]="file"
        ["src/main/java/$pkg_path/service/health/HealthEventService.java"]="file"
        ["src/main/java/$pkg_path/endpoint/rest/controller/health/HealthEventController.java"]="file"
        ["src/test/java/$pkg_path/conf/RabbitMQConf.java"]="file"
        ["src/test/java/$pkg_path/service/health/HealthEventServiceIT.java"]="file"
        ["src/test/java/$pkg_path/endpoint/rest/controller/health/HealthEventControllerIT.java"]="file"
    )
}

build_s3_bucket_files() {
    local pkg_path="$1"
    declare -gA S3_BUCKET_FILES=(
        ["src/main/java/$pkg_path/exception/bucket"]="directory"
        ["src/main/java/$pkg_path/config/BucketConf.java"]="file"
        ["src/main/java/$pkg_path/file/BucketComponent.java"]="file"
        ["src/main/java/$pkg_path/endpoint/rest/controller/health/HealthBucketController.java"]="file"
        ["src/main/java/$pkg_path/service/health/HealthBucketService.java"]="file"
        ["src/test/java/$pkg_path/conf/BucketConf.java"]="file"
        ["src/test/java/$pkg_path/file/BucketComponentIT.java"]="file"
        ["src/test/java/$pkg_path/service/health/HealthBucketServiceIT.java"]="file"
        ["src/test/java/$pkg_path/endpoint/rest/controller/health/HealthBucketControllerIT.java"]="file"
    )
}

build_email_files() {
    local pkg_path="$1"
    declare -gA EMAIL_FILES=(
        ["src/main/java/$pkg_path/mail"]="directory"
        ["src/test/java/$pkg_path/mail"]="directory"
        ["src/main/java/$pkg_path/config/EmailConf.java"]="file"
        ["src/main/java/$pkg_path/service/health/HealthEmailService.java"]="file"
        ["src/main/java/$pkg_path/exception/EmailSendException.java"]="file"
        ["src/main/java/$pkg_path/exception/health/EmailHealthCheckException.java"]="file"
        ["src/main/java/$pkg_path/endpoint/rest/controller/health/HealthEmailController.java"]="file"
        ["src/test/java/$pkg_path/conf/EmailConf.java"]="file"
        ["src/test/java/$pkg_path/service/health/HealthEmailServiceIT.java"]="file"
        ["src/test/java/$pkg_path/endpoint/rest/controller/health/HealthEmailControllerIT.java"]="file"
    )
}

# Check if a path exists and is of expected type
check_path_exists() {
    local project_dir="$1"
    local relative_path="$2"
    local expected_type="$3"
    local full_path="$project_dir/$relative_path"

    if ! validate_path "$full_path" "$project_dir"; then
        return 1
    fi

    if [ "$expected_type" = "file" ]; then
        [ -f "$full_path" ] && [ ! -L "$full_path" ]
    else
        [ -d "$full_path" ] && [ ! -L "$full_path" ]
    fi
}

# Validate that expected feature files exist
validate_feature_present() {
    local project_dir="$1"
    local feature="$2"
    local -n files_ref="$3"
    local errors=0

    print_info "Validating presence of $feature files..."

    for path in "${!files_ref[@]}"; do
        local expected_type="${files_ref[$path]}"

        if check_path_exists "$project_dir" "$path" "$expected_type"; then
            print_success "$feature: $expected_type exists: $path"
        else
            print_error "$feature: $expected_type missing: $path"
            ((errors++))
        fi
    done

    return $errors
}

# Validate that feature files do NOT exist
validate_feature_absent() {
    local project_dir="$1"
    local feature="$2"
    local -n files_ref="$3"
    local errors=0

    print_info "Validating absence of $feature files..."

    for path in "${!files_ref[@]}"; do
        local expected_type="${files_ref[$path]}"
        local full_path="$project_dir/$path"

        if [ -e "$full_path" ]; then
            print_error "$feature: $expected_type should not exist: $path"
            ((errors++))
        else
            print_success "$feature: $expected_type correctly absent: $path"
        fi
    done

    return $errors
}

validate_features() {
    local project_dir="$1"
    local group="$2"
    local artifact="$3"
    shift 3
    local enabled_features=("$@")
    local total_errors=0

    print_info "Group: $group, Artifact: $artifact"
    print_info "Enabled features: ${enabled_features[*]:-none}"
    echo ""

    local pkg_path
    pkg_path=$(package_to_path "$group" "$artifact")
    print_info "Package path: $pkg_path"
    echo ""

    build_postgresql_files "$pkg_path"
    build_rabbitmq_files "$pkg_path"
    build_s3_bucket_files "$pkg_path"
    build_email_files "$pkg_path"

    local feature
    for feature in "postgresql" "rabbitmq" "s3_bucket" "email"; do
        local feature_enabled=false

        for enabled in "${enabled_features[@]}"; do
            if [ "$enabled" = "$feature" ]; then
                feature_enabled=true
                break
            fi
        done

        case "$feature" in
            postgresql)
                if $feature_enabled; then
                    validate_feature_present "$project_dir" "PostgreSQL" POSTGRESQL_FILES || ((total_errors+=$?))
                else
                    validate_feature_absent "$project_dir" "PostgreSQL" POSTGRESQL_FILES || ((total_errors+=$?))
                fi
                ;;
            rabbitmq)
                if $feature_enabled; then
                    validate_feature_present "$project_dir" "RabbitMQ" RABBITMQ_FILES || ((total_errors+=$?))
                else
                    validate_feature_absent "$project_dir" "RabbitMQ" RABBITMQ_FILES || ((total_errors+=$?))
                fi
                ;;
            s3_bucket)
                if $feature_enabled; then
                    validate_feature_present "$project_dir" "S3_BUCKET" S3_BUCKET_FILES || ((total_errors+=$?))
                else
                    validate_feature_absent "$project_dir" "S3_BUCKET" S3_BUCKET_FILES || ((total_errors+=$?))
                fi
                ;;
            email)
                if $feature_enabled; then
                    validate_feature_present "$project_dir" "EMAIL" EMAIL_FILES || ((total_errors+=$?))
                else
                    validate_feature_absent "$project_dir" "EMAIL" EMAIL_FILES || ((total_errors+=$?))
                fi
                ;;
        esac
        echo ""
    done

    return $total_errors
}

export -f package_to_path
export -f build_postgresql_files
export -f build_rabbitmq_files
export -f build_s3_bucket_files
export -f build_email_files
export -f check_path_exists
export -f validate_feature_present
export -f validate_feature_absent
export -f validate_features
