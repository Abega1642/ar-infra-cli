# Contributing Guide

Thank you for your interest in contributing to this project.

This project prioritizes **security, maintainability, reliability, and consistency**.
All contributions must strictly follow the established rules and structure.

---

## Contribution Workflow

### 1. Fork the Repository

Navigate to the repository on GitHub and click the **Fork** button to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/ar-infra-cli.git
cd ar-infra-cli
```

### 3. Install Dependencies

Ensure you have **make** installed on your system. Then run:

```bash
make install-dev
```

This will install all development dependencies and configure the development environment.

### 4. Set Up Security Baseline

Generate the secrets baseline file:

```bash
detect-secrets scan > .secrets.baseline
```

### 5. Verify Installation

Run all tests to ensure your environment is properly configured:

```bash
make test
```

All tests must pass before proceeding.

### 6. Create a Feature Branch

Create a branch following the **Conventional Commits** naming convention:

```bash
git checkout -b feat/your-feature-name
```

Branch naming patterns:

- `feat/feature-name` for new features
- `fix/bug-description` for bug fixes
- `refactor/refactor-description` for refactoring
- `ci/ci-configuration-name` for CI/CD changes
- `docs/documentation-update` for documentation changes

### 7. Implement Your Changes

Make your code changes following the project structure and coding standards.

### 8. Run Tests

Verify your changes do not break existing functionality:

```bash
make test
```

All tests must pass.

### 9. Run Pre-Commit Checks

Execute all pre-commit hooks:

```bash
pre-commit run --all-files
```

This will run:

- Code formatting
- Linting
- Type checking
- Security scans
- Documentation checks

### 10. Address Pre-Commit Feedback

Refactor any code flagged by the pre-commit checks. Repeat step 9 until all checks pass.

### 11. Commit Your Changes

Commit using **Conventional Commits** format:

```bash
git commit -m "feat: add your feature description"
```

The commit will only succeed if all pre-commit filters pass. Commit message format:

```txt
feat: add content verification pipeline
fix: handle null metadata safely
refactor: simplify validation logic
docs: update contributing guide
ci: add new security scan
```

### 12. Push to Your Fork

```bash
git push origin feat/your-feature-name
```

### 13. Open a Pull Request

- Navigate to the original repository on GitHub
- Click **New Pull Request**
- Select your fork and branch
- Provide a clear description of your changes and motivation
- Submit the Pull Request

### 14. CI/CD Verification

All CI/CD checks must pass without exception:

- Build verification
- Test suite execution
- Code quality checks (Ruff, PyLint, MyPy)
- Security scans (CodeQL, Semgrep, Bandit)
- Documentation checks (PyDocStyle)

**If any check fails and is related to the core functionality of the project, the PR will be rejected.**

### 15. Review Process

- Your PR will be reviewed once all CI/CD checks pass
- Address any feedback from reviewers
- Approval is required before merge

---

## Project Structure Rules (Mandatory)

The existing project structure is **intentional** and **must be respected**.

- Do **NOT** introduce new directories or files that do not align with the current architecture
- Do **NOT** reorganize packages or folders without prior discussion
- Do **NOT** bypass existing abstractions or conventions

If you believe a structural change is necessary:

- Open a discussion **before** implementing it
- Provide clear technical justification

Unauthorized structural changes will be rejected.

---

## Code Quality & Security Requirements

All contributions **must**:

- Include appropriate tests
- Pass all CI checks:
  - Build
  - Tests
  - Formatting
  - CodeQL
  - Semgrep
  - MyPy
  - PyLint
  - Ruff
  - Bandit
  - PyDocStyle
- Maintain or improve:
  - Security
  - Maintainability
  - Reliability

All commits must fully pass the pre-commit filter before committing.
Any change that degrades these qualities will not be accepted.

---

## Commit Messages

Follow **Conventional Commits**:

```txt
feat: add content verification pipeline
fix: handle null metadata safely
refactor: simplify validation logic
refactor(readme): refactor last line
ci: update ci-test.yml
docs: add installation guide
```

---

## Pull Request Rules

- One logical change per Pull Request
- Clear description of the change and motivation
- CI **must** pass before review
- Approval is required before merge

---

## Security Issues

Security vulnerabilities must **not** be reported via public issues.

Please refer to [SECURITY.md](SECURITY.md).
