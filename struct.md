# Project Structure

````bash
src/ar_infra/
├── domain/                           # Pure business logic
│   ├── entities/
│   │   ├── project.py                # Project(group_id, artifact_id, name, description)
│   │   ├── gradle_dependency.py      # GradleDependency(group, name, version, configuration)
│   │   ├── java_package.py           # JavaPackage(base_path, segments)
│   │   └── generation_result.py      # Success/failure result
│   │
│   ├── value_objects/
│   │   ├── group_id.py               # e.g., "com.myorganization"
│   │   ├── artifact_id.py            # e.g., "myapp"
│   │   ├── package_name.py           # e.g., "com.myorganization.myapp"
│   │   ├── gradle_configuration.py   # implementation, testImplementation, etc.
│   │   └── github_repo_info.py       # owner, repo_name, visibility
│   │
│   ├── enums/
│   │   ├── generation_target.py      # LOCAL, GITHUB
│   │   ├── gradle_config.py          # IMPLEMENTATION, TEST_IMPLEMENTATION, etc.
│   │   └── database_type.py          # POSTGRESQL, MYSQL, H2
│   │
│   └── exceptions/
│       ├── domain_exception.py       # Base
│       ├── invalid_package_name.py
│       └── invalid_dependency.py
│
├── application/                      # Use cases + interfaces
│   ├── interfaces/
│   │   ├── repositories/
│   │   │   └── template_repository.py
│   │   │
│   │   └── services/
│   │       ├── template_fetcher.py           # ABC for fetching templates
│   │       ├── gradle_service.py             # ABC for Gradle operations
│   │       ├── java_package_service.py       # ABC for package renaming
│   │       ├── file_service.py               # ABC for file operations
│   │       ├── github_service.py             # ABC for GitHub operations
│   │       └── project_generator.py          # ABC for generation
│   │
│   ├── use_cases/
│   │   ├── generate_project/
│   │   │   ├── generate_local_project.py     # Generate locally
│   │   │   ├── generate_github_project.py    # Generate on GitHub
│   │   │   └── input_dto.py                  # Input data
│   │   │
│   │   ├── add_gradle_dependency/
│   │   │   ├── add_dependency.py
│   │   │   └── input_dto.py
│   │   │
│   │   └── validate_project/
│   │       ├── validate.py
│   │       └── validation_result.py
│   │
│   └── dto/
│       ├── project_config_dto.py
│       ├── generation_options_dto.py
│       └── github_config_dto.py
│
├── infrastructure/                   # Implementations
│   ├── templates/
│   │   ├── github_fetcher.py         # Fetch from your GitHub repo
│   │   ├── local_fetcher.py          # Use local cached template
│   │   └── template_cache.py
│   │
│   ├── gradle/
│   │   ├── gradle_parser.py          # Parse build.gradle (Groovy DSL)
│   │   ├── gradle_writer.py          # Modify build.gradle
│   │   ├── settings_gradle_writer.py # Modify settings.gradle
│   │   ├── dependency_injector.py    # Add dependencies
│   │   └── gradle_service_impl.py
│   │
│   ├── java/
│   │   ├── package_renamer.py        # Rename com.example.arInfra -> com.myorganization.myapp
│   │   ├── import_updater.py         # Update all import statements
│   │   └── java_package_service_impl.py
│   │
│   ├── file_processing/
│   │   ├── placeholder_replacer.py   # Replace {{ PROJECT_NAME }} in files
│   │   ├── file_copier.py
│   │   └── file_service_impl.py
│   │
│   ├── git/
│   │   ├── local_git.py              # Local git init, commit
│   │   └── github_client.py          # GitHub API (create repo, push)
│   │
│   └── generators/
│       ├── local_generator.py        # Generate in local filesystem
│       ├── github_generator.py       # Generate directly on GitHub
│       └── base_generator.py         # Shared logic
│
├── presentation/                     # CLI layer
│   ├── cli/
│   │   ├── app.py                    # Main Typer app
│   │   │
│   │   ├── commands/
│   │   │   ├── generate.py           # ar-infra generate [OPTIONS]
│   │   │   ├── add_dep.py            # ar-infra add-dep
│   │   │   ├── validate.py           # ar-infra validate
│   │   │   └── config.py             # ar-infra config (setup GitHub token, etc.)
│   │   │
│   │   └── options/
│   │       ├── generation_options.py
│   │       └── github_options.py
│   │
│   ├── interactive/
│   │   ├── prompts.py                # Questionary prompts
│   │   ├── collectors/
│   │   │   ├── project_collector.py  # Collect: group, artifact, name, description
│   │   │   ├── dependency_collector.py # Collect: dependencies to add
│   │   │   ├── database_collector.py  # Collect: DB type, credentials
│   │   │   └── github_collector.py    # Collect: repo name, visibility, auth
│   │   │
│   │   └── wizards/
│   │       ├── generation_wizard.py  # Full interactive flow
│   │       └── github_wizard.py
│   │
│   └── output/
│       ├── console.py                # Rich console
│       ├── progress.py               # Progress bars
│       └── formatters.py
│
├── config/
│   ├── settings.py                   # Pydantic settings
│   ├── constants.py                  # Template repo URL, default values
│   └── logging_config.py
│
└── utils/
    ├── file_utils.py
    ├── string_utils.py
    └── logger.py
\```
````
