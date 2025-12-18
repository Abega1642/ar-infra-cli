.PHONY: help install install-dev clean lint format type-check test test-cov security pre-commit build

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Ar-infra CLI - Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check src/ tests/
	isort --check-only src/ tests/

lint-fix: ## Run linters with auto-fix
	@echo "$(BLUE)Running linters with auto-fix...$(NC)"
	ruff check --fix src/ tests/
	isort src/ tests/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	black src/ tests/
	ruff format src/ tests/

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check src/ tests/
	ruff format --check src/ tests/

type-check: ## Run type checking
	@echo "$(BLUE)Running type checking...$(NC)"
	mypy src/

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=src/arinfra --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	@echo "$(BLUE)Running e2e tests...$(NC)"
	pytest tests/e2e/ -v

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	bandit -r src/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	pip-audit --requirement requirements.txt --format json --output pip-audit-report.json || true
	@echo "$(GREEN)Security reports generated$(NC)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	pre-commit autoupdate

ci: lint format-check type-check test security ## Run all CI checks locally
	@echo "$(GREEN)All CI checks passed!$(NC)"

build: clean ## Build package
	@echo "$(BLUE)Building package...$(NC)"
	python -m build

publish-test: build ## Publish to TestPyPI
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	python -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	@echo "$(YELLOW)WARNING: This will publish to PyPI!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python -m twine upload dist/*; \
	fi

dev-setup: install-dev ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@echo "$(GREEN)Development environment ready!$(NC)"

run: ## Run the CLI
	@echo "$(BLUE)Running ArInfra CLI...$(NC)"
	python -m arinfra

version: ## Show current version
	@python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])"
