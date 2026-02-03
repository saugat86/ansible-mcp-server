.PHONY: help install install-dev test lint format typecheck security pre-commit clean build release

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package dependencies
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test:  ## Run tests
	pytest -v

test-cov:  ## Run tests with coverage
	pytest -v --cov=ansible_mcp_server --cov-report=html --cov-report=term

lint:  ## Run linting
	ruff check .

lint-fix:  ## Run linting with auto-fix
	ruff check . --fix

format:  ## Format code
	ruff format .

format-check:  ## Check code formatting
	ruff format --check .

typecheck:  ## Run type checking
	mypy src/ansible_mcp_server --ignore-missing-imports

security:  ## Run security scan
	bandit -r src/ansible_mcp_server -c pyproject.toml

pre-commit:  ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-update:  ## Update pre-commit hooks
	pre-commit autoupdate

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	python -m build

build-check:  ## Build and check package
	python -m build
	twine check dist/*

release-test:  ## Release to Test PyPI
	python -m build
	twine upload --repository testpypi dist/*

release:  ## Release to PyPI (use with caution!)
	python -m build
	twine upload dist/*

verify:  ## Run all checks (lint, format, typecheck, security, test)
	@echo "Running format check..."
	@$(MAKE) format-check
	@echo "\nRunning linter..."
	@$(MAKE) lint
	@echo "\nRunning type checker..."
	@$(MAKE) typecheck
	@echo "\nRunning security scan..."
	@$(MAKE) security
	@echo "\nRunning tests..."
	@$(MAKE) test
	@echo "\n✅ All checks passed!"

ci:  ## Run CI checks locally
	@$(MAKE) verify

setup:  ## Initial project setup
	@echo "Setting up ansible-mcp-server development environment..."
	@$(MAKE) install-dev
	@echo "\n✅ Setup complete! Run 'make help' to see available commands."

ansible-check:  ## Verify Ansible installation
	@which ansible-playbook > /dev/null || (echo "❌ Ansible not installed"; exit 1)
	@ansible --version
	@ansible-playbook --version
	@echo "✅ Ansible is installed"

example-test:  ## Test example playbooks
	ansible-playbook playbooks/ping.yml --syntax-check
	ansible-playbook playbooks/system_info.yml --syntax-check
	ansible-inventory -i inventory/hosts.ini --list
	@echo "✅ Example playbooks are valid"
