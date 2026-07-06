# Changelog

All notable changes to AR-Infra CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-07-10

### Changed

- Feature-to-file mapping (directories, files, env variables, dependencies per `TemplateFeature`) moved from a hardcoded Python dict (`feature_files.py`) into `feature-conf.yml`, loaded through `FeatureConfigSchema` via `YamlFileProcessor`
- Config load result cached with `functools.cache` to avoid re-parsing YAML on repeated access

### Fixed

- Template file renames (e.g. `RabbitConfig.java` to `RabbitConf.java`) no longer require a Python source change, only a `feature-conf.yml` edit, before a new binary is built and released

## [0.2.0] - 2026-01-16

### Added in v0.2.0

- MySQL database support as an alternative to PostgreSQL
- Separate database selection workflow with dedicated prompts
- New `add-dependency` command for adding Gradle dependencies to existing projects
- `--no-feature` flag to generate minimal Spring Boot projects without infrastructure features
- SwaggerHandler for automatic OpenAPI specification cleanup based on selected features
- Template repository tag-based cloning for version compatibility
- Enhanced feature selection with distinct database and infrastructure component steps

### Changed in v0.2.0

- Feature selection workflow now separates database choice from other infrastructure components
- Template cloning now targets specific version tags to maintain backward and forward compatibility
- OpenAPI documentation (doc/api.yml) now updates dynamically based on selected features
- Improved project generation flow with clearer separation of concerns

### Fixed in v0.2.0

- OpenAPI specification files now properly reflect selected infrastructure features
- Template compatibility issues between CLI versions resolved through tag-based cloning
- Unused OpenAPI endpoints are now removed when corresponding features are not selected

## [0.1.3] - 2026-01-12

### Added v0.1.3

- GitHub App integration (ar-infra-bot) for automated repository setup
- Automatic GitHub authorization workflow during project generation
- Pre-configured CI/CD workflows (CodeQL and Semgrep) that work out-of-the-box
- New `--skip-github-app` flag to bypass GitHub App integration when needed
- Enhanced CLI user interface with improved messaging and feedback

### Changed in v0.1.3

- Project generation now includes GitHub repository configuration step
- Improved user experience with clearer status messages and prompts
- Enhanced formatting workflow to handle projects with no features selected

### Fixed in v0.1.3

- CodeQL and Semgrep CI workflows now function correctly with proper GitHub authorization
- Project formatting no longer fails when no infrastructure features are selected
- Resolved authorization issues that previously caused CI pipeline failures

## [0.1.2] - 2026-01-10

### Added in v0.1.2

- Comprehensive logging system throughout project generation workflow
- Detailed progress tracking with step-by-step updates
- Windows `.bat` file support for dual-shell compatibility (CMD and Bash)
- Enhanced error reporting with clear, actionable messages
- Process visibility showing which step is executing during generation
- Build-time secret injection for improved security

### Changed in v0.1.2

- Improved project generation workflow with better user feedback
- Enhanced Windows support with native batch script handling
- Secrets are now injected at build time instead of being bundled in binaries
- Updated security model to prevent secret extraction from distributed binaries

### Fixed in v0.1.2

- Missing banner in PyPI package installations
- Resource file inclusion in Python package distribution
- Inconsistencies between binary and PyPI package contents
- Windows users can now execute format scripts with both CMD and Bash shells

### Security

- Removed `.env` file dependency from binary distributions
- Implemented secure build-time configuration injection
- Enhanced CI/CD security gates
- Reduced risk of secret extraction from binaries

## [0.1.1] - 2026-01-07

### Features

- Initial stable release of AR-Infra CLI
- Interactive project initialization with guided prompts
- Command-line interface for automated project generation
- PostgreSQL database integration support
- RabbitMQ message broker integration support
- AWS S3-compatible (BackBlaze) bucket configuration support
- Email service configuration support
- Cross-platform binary distribution (Linux, macOS Intel/ARM, Windows)
- PyPI package distribution
- SHA256 checksum verification for binary releases
- GitHub Actions automated release workflow
- PyInstaller-based binary compilation

### Infrastructure

- GitHub Actions CI/CD pipeline for releases
- Multi-platform binary builds (Linux x64, macOS x64/ARM64, Windows x64)
- PyPI publishing automation
- Security verification gates in release process

### Documentation

- Comprehensive README with installation and usage instructions
- Release notes structure for version tracking
- API documentation via command-line help system

[0.2.1]: https://github.com/Abega1642/ar-infra-cli/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/Abega1642/ar-infra-cli/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/Abega1642/ar-infra-cli/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Abega1642/ar-infra-cli/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Abega1642/ar-infra-cli/releases/tag/v0.1.1
