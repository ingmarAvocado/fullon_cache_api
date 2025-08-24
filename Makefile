.PHONY: help setup install test lint format clean dev docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial setup for development
	@echo "Setting up development environment..."
	poetry install
	poetry run pre-commit install
	cp .env.example .env || echo "⚠️  No .env.example found - create .env manually"
	@echo "✅ Setup complete! Edit .env file with your Redis credentials."

install: ## Install dependencies
	poetry install

test: ## Run all tests
	poetry run python run_test.py

test-cov: ## Run tests with coverage
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	poetry run pytest -f

lint: ## Run linting
	poetry run ruff check .
	poetry run mypy src/

format: ## Format code
	poetry run black .
	poetry run ruff --fix .

clean: ## Clean cache and build artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

dev: ## Run development server
	poetry run uvicorn src.fullon_cache_api.main:app --reload --host 0.0.0.0 --port 8000

prod: ## Run production server
	poetry run uvicorn src.fullon_cache_api.main:app --host 0.0.0.0 --port 8000

check: ## Run all checks (lint, test, format check)
	poetry run black --check .
	poetry run ruff check .
	poetry run mypy src/
	poetry run python run_test.py

pre-commit: ## Run pre-commit hooks
	poetry run pre-commit run --all-files

docker-build: ## Build Docker image
	docker build -t fullon_cache_api .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env fullon_cache_api

# Development helpers
shell: ## Start poetry shell
	poetry shell

deps-update: ## Update dependencies
	poetry update

deps-show: ## Show dependency tree
	poetry show --tree