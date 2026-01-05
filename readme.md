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
  <img src="https://img.shields.io/badge/version-0.1.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/CLI-Typer-000000?style=for-the-badge" />
</p>

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,java,spring,gradle,docker,postgres,rabbitmq,github&theme=light" />
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
- [What is ar-infra?](#what-is-ar-infra)
- [What is ar-infra-template?](#what-is-ar-infra-template)
- [What is ar-infra-cli?](#what-is-ar-infra-cli)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Command Line Mode](#command-line-mode)
  - [Available Options](#available-options)
  - [Feature Flags](#feature-flags)
- [Examples](#examples)
- [Generated Project Structure](#generated-project-structure)
- [Conclusion](#conclusion)

---

## Introduction

The **ar-infra-cli** is a command-line tool designed to generate **production-ready Spring Boot applications**. It leverages the [ar-infra-template](https://github.com/Abega1642/ar-infra-template.git) as its foundation, ensuring that every generated project starts with a complete, enterprise-grade infrastructure.

This CLI automates the creation of new backend services, eliminating the repetitive setup work and enforcing consistent architecture and security practices across projects.

---

## What is ar-infra?

**ar-infra** refers to the architecture and infrastructure baseline defined by this ecosystem. It represents a structured, production-ready backend stack that includes:

- Messaging (RabbitMQ)
- Storage (S3-compatible bucket)
- Database (PostgreSQL with Flyway migrations)
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
- **Feature selection** (add or remove components as needed)
- **Target location** customization

By running a single command, developers can bootstrap a fully configured Spring Boot application based on the ar-infra architecture without manual setup.

---

## Usage

The **ar-infra-cli** provides a single command: `ar-infra init`. This command can be used in two modes: interactive or command-line.

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
- Features to include or exclude

### Command Line Mode

For automation or quick generation, all options can be provided directly via command-line flags.

```bash
ar-infra init --group=com.example --artifact=myapp --project-version=1.0.0
```

### Available Options

| Option               | Description                                 | Example                |
| -------------------- | ------------------------------------------- | ---------------------- |
| `--group`            | Maven group ID for the project              | `com.example`          |
| `--artifact`         | Maven artifact ID for the project           | `backend-api`          |
| `--project-version`  | Version of the generated project            | `1.0.0`                |
| `--path`             | Directory where the project will be created | `/home/user/projects`  |
| `--project-dir`      | Name of the project directory               | `my-project`           |
| `--features`         | Comma-separated list of features to include | `postgresql,s3_bucket` |
| `--disable-features` | Comma-separated list of features to exclude | `rabbitmq,email`       |

### Feature Flags

The following features can be enabled or disabled during project generation:

| Feature      | Description                                        |
| ------------ | -------------------------------------------------- |
| `postgresql` | PostgreSQL database support with Flyway migrations |
| `rabbitmq`   | RabbitMQ message broker integration                |
| `s3_bucket`  | AWS S3-compatible storage integration              |
| `email`      | Email sending capabilities                         |

By default, all features are enabled. Use `--disable-features` to exclude specific components.

---

## Examples

### Basic Usage

Generate a project with default settings in interactive mode:

```bash
ar-infra init
```

### Quick Start

Generate a project with minimal configuration:

```bash
ar-infra init --group=com.mycompany --artifact=backend-api
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
    --features=postgresql,s3_bucket
```

### Minimal Configuration

Generate a project without messaging and email features:

```bash
ar-infra init \
    --group=com.example \
    --artifact=minimal-api \
    --disable-features=rabbitmq,email
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
- OpenAPI documentation
- Security configuration
- Database migration scripts (Flyway)
- Message broker configuration
- S3 storage integration
- Email service configuration

---

## Conclusion

The **ar-infra-cli** is the entry point for teams adopting the ar-infra architecture. By combining the solid foundation of **ar-infra-template** with the automation of a CLI tool, it enables developers to start new backend projects quickly, consistently, and securely.

This tool is maintained by **Abegà Razafindratelo**. For questions, issues, or contributions, please refer to the project repository or contact directly at [a.razafindratelo@gmail.com](mailto:a.razafindratelo@gmail.com).

For more information, visit the [ar-infra-template repository](https://github.com/Abega1642/ar-infra-template).
