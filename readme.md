<p align="center">
  <img src="ar-infra-logo.png" alt="ar-infra-cli logo" width="400"/>
</p>

<h1 align="center">ar-infra-cli</h1>

<p align="center">
  <strong>CLI generator for production-ready Spring Boot backends</strong><br/>
  Opinionated infrastructure scaffolding powered by ar-infra-template
</p>

<p align="center">
  <a href="https://github.com/Abega1642/ar-infra-cli/actions">
    <img src="https://img.shields.io/badge/ci%2Fcd-passing-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white" />
  </a>
  <a href="https://github.com/Abega1642/ar-infra-cli/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Abega1642/ar-infra-cli?style=for-the-badge" />
  </a>
  <img src="https://img.shields.io/badge/version-0.2.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/CLI-Typer-000000?style=for-the-badge" />
</p>

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,java,spring,gradle,docker,postgres,mysql,rabbitmq,github&theme=light" />
</p>

<p align="center">
  <sub>Designed & maintained by <a href="https://github.com/Abega1642">Abegà Razafindratelo</a></sub>
</p>

---

<p align="center">
  <img src="ar-infra-cli-banner.png" alt="ar-infra-cli banner" width="50%"/>
</p>

---

## Table of Contents

- [Introduction](#introduction)
- [What's New in v0.2.0](#whats-new-in-v020)
- [What is ar-infra?](#what-is-ar-infra)
- [What is ar-infra-template?](#what-is-ar-infra-template)
- [What is ar-infra-cli?](#what-is-ar-infra-cli)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Command Line Mode](#command-line-mode)
  - [Adding Dependencies](#adding-dependencies)
  - [Available Options](#available-options)
  - [Feature Flags](#feature-flags)
- [Examples](#examples)
- [Generated Project Structure](#generated-project-structure)
- [System Requirements](#system-requirements)
- [Conclusion](#conclusion)

---

## Introduction

The **ar-infra-cli** is a command-line tool designed to generate **production-ready Spring Boot applications**. It leverages the [ar-infra-template](https://github.com/Abega1642/ar-infra-template.git) as its foundation, ensuring that every generated project starts with a complete, enterprise-grade infrastructure.

This CLI automates the creation of new backend services, eliminating the repetitive setup work and enforcing consistent architecture and security practices across projects.

---

## What's New in v0.2.0

### MySQL Database Support

- **Multiple database options**: Choose between PostgreSQL and MySQL during project initialization
- **Dedicated database selection workflow**: Database choice is now a separate step with clear prompts
- **Full MySQL integration**: Connection pooling, migrations, and entity management configured automatically

### New `add-dependency` Command

- **Gradle dependency management**: Add dependencies to existing projects without manual file editing
- **Single or batch additions**: Add one dependency or multiple in a single command
- **Project path flexibility**: Specify custom project paths or use current directory

### Enhanced OpenAPI Documentation Handling

- **Dynamic specification cleanup**: OpenAPI documentation (doc/api.yml) now updates based on selected features
- **SwaggerHandler integration**: Automatically removes unused API endpoints for non-selected features
- **Accurate documentation**: Generated API specifications reflect only the enabled infrastructure components

### Template Version Compatibility

- **Tag-based cloning**: CLI now clones specific template repository versions using Git tags
- **Backward compatibility**: Older CLI versions continue to work with their corresponding template versions
- **Forward compatibility**: New template updates won't break existing CLI installations

### Streamlined Feature Selection

- **Two-step selection process**: Database choice separated from other infrastructure features
- **Zero-feature option**: New `--no-feature` flag generates minimal Spring Boot projects
- **Better workflow**: More intuitive feature selection aligned with project needs

---

## What is ar-infra?

**ar-infra** refers to the architecture and infrastructure baseline defined by this ecosystem. It represents a structured, production-ready backend stack that includes:

- Messaging (RabbitMQ)
- Storage (S3-compatible bucket)
- Database (PostgreSQL or MySQL with Flyway migrations)
- Email service
- Security configuration
- Health check endpoints
- Integration testing with Testcontainers
- CI/CD workflows
- Dockerized runtime environment
- OpenAPI documentation with Swagger UI

This architecture is designed to be reliable, maintainable, and secure, suitable for enterprise-scale applications.

---

## What is ar-infra-template?

The [ar-infra-template](https://github.com/Abega1642/ar-infra-template.git) is the **base template** that implements the ar-infra architecture. It provides the full project structure, configurations, validators, health endpoints, and CI/CD pipelines.

It is not intended to be cloned and customized manually. Instead, it serves as the **foundation** for generated projects, ensuring that every new application starts with the same solid infrastructure.

For more information about the ar-infra architecture, visit the [ar-infra-template repository](https://github.com/Abega1642/ar-infra-template.git).

---

## What is ar-infra-cli?

The **ar-infra-cli** is the tool that generates new Spring Boot projects based on the ar-infra-template. It provides customization options such as:

- **groupId** and **artifactId**
- **Project version**
- **Database selection** (PostgreSQL or MySQL)
- **Feature selection** (add or remove components as needed)
- **Target location** customization
- **GitHub App integration** for automated CI/CD setup
- **Dependency management** for existing projects

By running a single command, developers can bootstrap a fully configured Spring Boot application based on the ar-infra architecture without manual setup.

---

## Installation

### Binary Installation (Recommended)

#### Linux (x64)

```bash
curl -LO https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-linux-amd64
curl -LO https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-linux-amd64.sha256
shasum -a 256 -c ar-infra-linux-amd64.sha256
chmod +x ar-infra-linux-amd64
sudo mv ar-infra-linux-amd64 /usr/local/bin/ar-infra
```

#### macOS (Intel)

```bash
curl -LO https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-macos-amd64
curl -LO https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-macos-amd64.sha256
shasum -a 256 -c ar-infra-macos-amd64.sha256
chmod +x ar-infra-macos-amd64
sudo mv ar-infra-macos-amd64 /usr/local/bin/ar-infra
```

#### macOS (Apple Silicon)

```bash
curl -LO https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-macos-arm64
curl -LO https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-macos-arm64.sha256
shasum -a 256 -c ar-infra-macos-arm64.sha256
chmod +x ar-infra-macos-arm64
sudo mv ar-infra-macos-arm64 /usr/local/bin/ar-infra
```

#### Windows (PowerShell as Administrator)

```powershell
Invoke-WebRequest -Uri "https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-windows-amd64.exe" -OutFile "ar-infra.exe"
Invoke-WebRequest -Uri "https://github.com/Abega1642/ar-infra-cli/releases/download/v0.2.0/ar-infra-windows-amd64.exe.sha256" -OutFile "ar-infra.exe.sha256"
certutil -hashfile ar-infra.exe SHA256
Move-Item ar-infra.exe C:\Windows\System32\ar-infra.exe
```

### Python Package Installation

Using pipx (recommended for CLI tools):

```bash
pipx install ar-infra-cli
```

Using pip:

```bash
pip install ar-infra-cli
```

---

## Usage

The **ar-infra-cli** provides two main commands: `ar-infra init` for project generation and `ar-infra add-dependency` for dependency management.

### Interactive Mode

The interactive mode guides you through project setup with prompts for each configuration option. This is the recommended approach for first-time users.

```bash
ar-infra init
```

The CLI will ask you to provide:

- Group ID (e.g., `com.example`)
- Artifact ID (e.g., `myapp`)
- Project version (e.g., `1.0.0`)
- Output path
- Database choice (PostgreSQL, MySQL, or none)
- Additional features to include or exclude
- GitHub repository setup (optional)

When you choose to push your project to a repository, the CLI will guide you through automated authorization via the ar-infra-bot GitHub App, ensuring your CI/CD workflows work immediately.

### Command Line Mode

For automation or quick generation, all options can be provided directly via command-line flags.

```bash
ar-infra init --group=com.example --artifact=myapp --project-version=1.0.0
```

Generate a project with MySQL and specific features:

```bash
ar-infra init \
  --group=com.example \
  --artifact=backend-api \
  --features=mysql,rabbitmq,s3_bucket
```

Generate a minimal project with no infrastructure features:

```bash
ar-infra init \
  --group=com.example \
  --artifact=minimal-app \
  --no-feature
```

Skip GitHub App integration if you don't need CI/CD setup:

```bash
ar-infra init \
  --group=com.example \
  --artifact=backend-api \
  --skip-github-app
```

### Adding Dependencies

The `add-dependency` command allows you to add Gradle dependencies to existing projects.

#### Add a single dependency

```bash
ar-infra add-dependency "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'"
```

#### Add multiple dependencies

```bash
ar-infra add-dependency \
  "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'" \
  "runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'" \
  "runtimeOnly 'io.jsonwebtoken:jjwt-jackson:0.13.0'"
```

#### Add dependency to specific project

```bash
ar-infra add-dependency \
  --project-path /path/to/project \
  "implementation 'org.springframework.boot:spring-boot-starter-data-jpa'"
```

### Available Options

#### `init` Command Options

| Option               | Description                                 | Example               |
| -------------------- | ------------------------------------------- | --------------------- |
| `--group`            | Maven group ID for the project              | `com.example`         |
| `--artifact`         | Maven artifact ID for the project           | `backend-api`         |
| `--project-version`  | Version of the generated project            | `1.0.0`               |
| `--path`             | Directory where the project will be created | `/home/user/projects` |
| `--project-dir`      | Name of the project directory               | `my-project`          |
| `--features`         | Comma-separated list of features to include | `mysql,rabbitmq`      |
| `--disable-features` | Comma-separated list of features to exclude | `rabbitmq,email`      |
| `--no-feature`       | Generate project without any features       | N/A                   |
| `--no-cache`         | Skip template caching and fetch fresh       | N/A                   |
| `--skip-github-app`  | Skip GitHub App integration                 | N/A                   |

#### `add-dependency` Command Options

| Option           | Description                           | Example            |
| ---------------- | ------------------------------------- | ------------------ |
| `--project-path` | Path to the project root              | `/path/to/project` |
| Dependencies     | One or more Gradle dependency strings | See examples above |

### Feature Flags

The following features can be enabled or disabled during project generation:

#### Database Options (Choose One or None)

| Feature      | Description                                        |
| ------------ | -------------------------------------------------- |
| `postgresql` | PostgreSQL database support with Flyway migrations |
| `mysql`      | MySQL database support with Flyway migrations      |

#### Additional Infrastructure Features

| Feature     | Description                                       |
| ----------- | ------------------------------------------------- |
| `rabbitmq`  | RabbitMQ message broker integration               |
| `s3_bucket` | AWS S3-compatible storage integration (BackBlaze) |
| `email`     | Email sending capabilities                        |

By default, all features are enabled. Use `--disable-features` to exclude specific components, or use `--no-feature` to generate a minimal Spring Boot application.

---

## Examples

### Basic Usage

Generate a project with default settings in interactive mode:

```bash
ar-infra init
```

### Quick Start with MySQL

Generate a project with MySQL database:

```bash
ar-infra init --group=com.mycompany --artifact=backend-api --features=mysql
```

### Full Customization

Generate a project with all options specified:

```bash
ar-infra init \
    --group=dev.razafindratelo \
    --artifact=cool-project \
    --project-version=2.0.0 \
    --path=/home/user/projects \
    --project-dir=cool-project \
    --features=postgresql,s3_bucket,rabbitmq
```

### Minimal Configuration

Generate a minimal Spring Boot project without any infrastructure:

```bash
ar-infra init \
    --group=com.example \
    --artifact=minimal-api \
    --no-feature
```

### Fresh Template Fetch

Generate a project with fresh template (bypass cache):

```bash
ar-infra init \
    --group=com.example \
    --artifact=myapp \
    --no-cache
```

### Add JWT Dependencies

Add JWT authentication dependencies to an existing project:

```bash
ar-infra add-dependency \
  "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'" \
  "runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'" \
  "runtimeOnly 'io.jsonwebtoken:jjwt-jackson:0.13.0'"
```

---

## Generated Project Structure

Projects generated by **ar-infra-cli** include:

- Complete Spring Boot application structure
- Gradle build configuration
- Docker and Docker Compose setup
- CI/CD workflows (GitHub Actions)
- Integration tests with Testcontainers
- Health check endpoints
- OpenAPI documentation (dynamically configured)
- Security configuration
- Database migration scripts (Flyway)
- Message broker configuration (optional)
- S3 storage integration (optional)
- Email service configuration (optional)

---

## System Requirements

### Binary Distribution

- **Linux**: x86_64 architecture, GLIBC 2.17+
- **macOS**: 10.13+ (Intel), 11.0+ (Apple Silicon)
- **Windows**: Windows 10/11, x86_64 architecture

### Python Package

- **Python**: 3.11 or higher
- **Package Manager**: pip or pipx

### Additional Requirements

- Internet connectivity for GitHub App integration (optional)
- Git installed for repository operations

---

## Conclusion

The **ar-infra-cli** is the entry point for teams adopting the ar-infra architecture. By combining the solid foundation of **ar-infra-template** with the automation of a CLI tool, it enables developers to start new backend projects quickly, consistently, and securely.

With v0.2.0, MySQL support provides database flexibility, the new `add-dependency` command simplifies dependency management, and tag-based template versioning ensures long-term compatibility across CLI versions.

This tool is maintained by **Abegà Razafindratelo**. For questions, issues, or contributions, please refer to the project repository or contact directly at [a.razafindratelo@gmail.com](mailto:a.razafindratelo@gmail.com).

For more information, visit the [ar-infra-template repository](https://github.com/Abega1642/ar-infra-template).

---

## Support and Documentation

- **Repository**: [https://github.com/Abega1642/ar-infra-cli](https://github.com/Abega1642/ar-infra-cli)
- **Issue Tracker**: [https://github.com/Abega1642/ar-infra-cli/issues](https://github.com/Abega1642/ar-infra-cli/issues)
- **Template Repository**: [https://github.com/Abega1642/ar-infra-template](https://github.com/Abega1642/ar-infra-template)
- **GitHub App**: ar-infra-bot (installation guided during project setup)

---

## Security Considerations

- Binary integrity verification via SHA256 checksums is strongly recommended
- All binaries are built via GitHub Actions with full transparency
- Secrets are injected at build time rather than bundled, improving security
- The ar-infra-bot GitHub App uses minimal, scoped permissions
- No code signing is provided; users should verify checksums before execution
- Source code is available for audit
- Template version tags ensure predictable and auditable project generation
