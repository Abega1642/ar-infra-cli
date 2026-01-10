# Changelog

All notable changes to AR-Infra CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-01-10

### Added

- Comprehensive logging system throughout project generation workflow
- Detailed progress tracking with step-by-step updates
- Windows `.bat` file support for dual-shell compatibility (CMD and Bash)
- Enhanced error reporting with clear, actionable messages
- Process visibility showing which step is executing during generation
- Build-time secret injection for improved security

### Changed

- Improved project generation workflow with better user feedback
- Enhanced Windows support with native batch script handling
- Secrets are now injected at build time instead of being bundled in binaries
- Updated security model to prevent secret extraction from distributed binaries

### Fixed

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

[0.1.2]: https://github.com/Abega1642/ar-infra-cli/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Abega1642/ar-infra-cli/releases/tag/v0.1.1
