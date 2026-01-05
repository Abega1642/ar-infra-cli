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

## 1. Introduction

The **ar‑infra‑cli** is a command‑line tool designed to generate **production‑ready Spring Boot applications**. It leverages the [ar‑infra‑template](https://github.com/Abega1642/ar-infra-template.git) as its foundation, ensuring that every generated project starts with a complete, enterprise‑grade infrastructure.

This CLI automates the creation of new backend services, eliminating the repetitive setup work and enforcing consistent architecture and security practices across projects.

---

## 2. What is ar‑infra?

**ar‑infra** refers to the architecture and infrastructure baseline defined by this ecosystem. It represents a structured, production‑ready backend stack that includes:

- Messaging (RabbitMQ)
- Storage (S3‑compatible bucket)
- Database (PostgreSQL with Flyway migrations)
- Email service
- Security configuration
- Health check endpoints
- Integration testing with Testcontainers
- CI/CD workflows
- Dockerized runtime environment
- OpenAPI documentation with Swagger UI

This architecture is designed to be reliable, maintainable, and secure, suitable for enterprise‑scale applications.

---

## 3. What is ar‑infra‑template?

The [ar‑infra‑template](https://github.com/Abega1642/ar-infra-template.git) is the **base template** that implements the ar‑infra architecture. It provides the full project structure, configurations, validators, health endpoints, and CI/CD pipelines.

It is not intended to be cloned and customized manually. Instead, it serves as the **foundation** for generated projects, ensuring that every new application starts with the same solid infrastructure.

---

## 4. What is ar‑infra‑cli?

The **ar‑infra‑cli** is the tool that makes ar‑infra practical. It generates new Spring Boot projects based on the ar‑infra‑template, with customization options such as:

- **groupId** and **artifactId**
- **Dependencies** (add or remove as needed)
- **Target location**: generate locally on your computer, or both locally and directly in your GitHub account
- **Configuration options** for tailoring the generated project to your team’s needs

By running a single command, developers can bootstrap a fully configured, production‑ready Spring Boot application without manual setup.

---

## 5. Current Status

The **ar‑infra‑cli** project is **under active development**.

Future documentation will include:

- How to download and install the CLI
- How to use it to generate projects
- Examples of customization options

At this stage, the README serves to explain the purpose and scope of the tool. Usage instructions will be added once the CLI reaches a stable release.

---

## 6. Conclusion

The **ar‑infra‑cli** is the entry point for teams adopting the ar‑infra architecture. By combining the solid foundation of **ar‑infra‑template** with the automation of a CLI tool, it enables developers to start new backend projects quickly, consistently, and securely.

This ecosystem demonstrates readiness for enterprise projects, ensuring that every generated application is production‑ready from day one.
