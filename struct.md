# Project Structure

````bash
ar-infra-cli/
├── .github/
│   ├── workflows/
│   │   ├── lint.yml                    # Ruff linter (fastest Python linter)
│   │   ├── codeql-analysis.yml         # CodeQL security analysis
│   │   ├── format-check.yml            # Black formatter check
│   │   ├── type-check.yml              # mypy static type checking
│   │   ├── tests.yml                   # pytest with coverage
│   │   ├── security-scan.yml           # Bandit + Safety checks
│   │   └── ci.yml                      # Main CI pipeline (orchestrates all)
│   ├── dependabot.yml                  # Automated dependency updates
│   └── CODEOWNERS                      # Code ownership
│
├── src/
│   └── ar_infra/
│       ├── __init__.py
│       ├── __main__.py                 # Entry point for `python -m arinfra`
│       │
│       ├── cli/                        # CLI Layer (Interface)
│       │   ├── __init__.py
│       │   ├── app.py                  # Main Typer app
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── create.py           # Create project command
│       │   │   ├── add_dependency.py   # Add dependency command
│       │   │   ├── configure.py        # Configuration command
│       │   │   └── validate.py         # Validate existing project
│       │   └── utils/
│       │       ├── __init__.py
│       │       ├── validators.py       # Input validation
│       │       ├── prompts.py          # Interactive prompts
│       │       └── output.py           # Rich console output formatting
│       │
│       ├── core/                       # Business Logic (Use Cases)
│       │   ├── __init__.py
│       │   ├── interfaces/             # Abstract interfaces (DIP)
│       │   │   ├── __init__.py
│       │   │   ├── template_fetcher.py
│       │   │   ├── file_processor.py
│       │   │   ├── dependency_manager.py
│       │   │   └── project_generator.py
│       │   │
│       │   ├── use_cases/              # Business logic
│       │   │   ├── __init__.py
│       │   │   ├── create_project.py
│       │   │   ├── add_dependency.py
│       │   │   ├── customize_project.py
│       │   │   └── validate_project.py
│       │   │
│       │   ├── entities/               # Domain models
│       │   │   ├── __init__.py
│       │   │   ├── project_config.py   # Project configuration entity
│       │   │   ├── dependency.py       # Dependency entity
│       │   │   ├── template.py         # Template entity
│       │   │   └── package_info.py     # Package information
│       │   │
│       │   └── exceptions/             # Custom exceptions
│       │       ├── __init__.py
│       │       ├── template_errors.py
│       │       ├── validation_errors.py
│       │       └── processing_errors.py
│       │
│       ├── infrastructure/             # External adapters (Implementation)
│       │   ├── __init__.py
│       │   ├── template/
│       │   │   ├── __init__.py
│       │   │   ├── github_fetcher.py   # GitHub template fetcher
│       │   │   └── local_fetcher.py    # Local template (for dev)
│       │   │
│       │   ├── processors/
│       │   │   ├── __init__.py
│       │   │   ├── package_processor.py    # Package renaming
│       │   │   ├── import_processor.py     # Import statement updates
│       │   │   ├── placeholder_processor.py # Template variable replacement
│       │   │   └── file_structure_processor.py # Directory operations
│       │   │
│       │   ├── gradle/
│       │   │   ├── __init__.py
│       │   │   ├── dependency_injector.py  # Add dependencies to build.gradle
│       │   │   ├── gradle_parser.py        # Parse gradle files
│       │   │   └── gradle_formatter.py     # Format gradle files
│       │   │
│       │   └── git/
│       │       ├── __init__.py
│       │       └── repository.py           # Git operations
│       │
│       ├── config/                     # Configuration
│       │   ├── __init__.py
│       │   ├── settings.py             # Application settings (Pydantic)
│       │   ├── logging_config.py       # Logging configuration
│       │   └── templates_config.py     # Template configurations
│       │
│       └── utils/                      # Shared utilities
│           ├── __init__.py
│           ├── file_utils.py           # File operations
│           ├── string_utils.py         # String manipulation
│           ├── validation_utils.py     # Common validations
│           └── logger.py               # Custom logger
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # pytest fixtures
│   │
│   ├── unit/                           # Unit tests
│   │   ├── __init__.py
│   │   ├── test_entities/
│   │   ├── test_use_cases/
│   │   ├── test_processors/
│   │   └── test_utils/
│   │
│   ├── integration/                    # Integration tests
│   │   ├── __init__.py
│   │   ├── test_template_fetching/
│   │   ├── test_project_generation/
│   │   └── test_gradle_operations/
│   │
│   ├── e2e/                           # End-to-end tests
│   │   ├── __init__.py
│   │   └── test_full_workflow.py
│   │
│   └── fixtures/                       # Test data
│       ├── sample_template/
│       ├── sample_gradle_files/
│       └── mock_responses/
│
├── docs/
│   ├── architecture/
│   │   ├── ADR/                        # Architecture Decision Records
│   │   │   ├── 001-cli-framework.md
│   │   │   ├── 002-clean-architecture.md
│   │   │   └── 003-dependency-injection.md
│   │   ├── diagrams/
│   │   └── design.md
│   ├── api/                            # API documentation
│   ├── user-guide/
│   │   ├── installation.md
│   │   ├── quick-start.md
│   │   └── advanced-usage.md
│   └── development/
│       ├── contributing.md
│       ├── setup.md
│       └── testing.md
│
├── scripts/
│   ├── setup_dev.sh                    # Development environment setup
│   ├── run_tests.sh                    # Test runner script
│   └── build.sh                        # Build script
│
├── .gitignore
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .editorconfig                      # Editor configuration
├── .bandit                            # Bandit security config
├── pyproject.toml                     # Project metadata + tool configs
├── requirements.txt                   # Production dependencies
├── requirements-dev.txt               # Development dependencies
├── setup.py                           # Package setup
├── README.md
├── CHANGELOG.md
├── LICENSE
├── SECURITY.md                        # Security policy
└── CODE_OF_CONDUCT.md
\```
````
