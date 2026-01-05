HELP_TEXT = """
AR-INFRA - Spring Boot Project Generator

USAGE:
    ar-infra init [OPTIONS]

DESCRIPTION:
    Generate a production-ready Spring Boot project with customizable features.
    You can use interactive mode or provide all options via command line.

INTERACTIVE MODE:
    ar-infra init

    Guides you through project setup with beautiful prompts.

COMMAND LINE MODE:
    ar-infra init --group=com.example --artifact=myapp --version=1.0.0

OPTIONS:
    --group TEXT              Maven group ID (e.g., com.example, dev.mycompany)
    --artifact TEXT           Maven artifact ID (project name)
    --version TEXT            Project version (default: 1.0.0)
    --path PATH               Destination directory (default: current directory)
    --features TEXT           Comma-separated features to enable
                             Available: postgresql, rabbitmq, s3_bucket, email
    --no-features TEXT        Comma-separated features to disable
    --template-url TEXT       Custom template repository URL
    --no-cache               Don't use cached template
    --help                   Show this help message

EXAMPLES:
    # Interactive mode (recommended for first-time users)
    ar-infra init

    # Quick start with defaults
    ar-infra init --group=com.mycompany --artifact=backend-api

    # Full customization
    ar-infra init \\
        --group=dev.razafindratelo \\
        --artifact=cool-project \\
        --version=2.0.0 \\
        --path=/home/user/projects \\
        --features=postgresql,s3_bucket

    # Exclude specific features
    ar-infra init \\
        --group=com.example \\
        --artifact=minimal-api \\
        --no-features=rabbitmq,email

FEATURES:
    postgresql    PostgreSQL database support
    rabbitmq      RabbitMQ message broker
    s3_bucket     AWS S3 integration
    email         Email sending capabilities

For more information, visit: https://github.com/Abega1642/ar-infra-template
"""
