.PHONY: help lint format typecheck check run clean install

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync

lint:  ## Run linting checks
	uv run ruff check src/

format:  ## Format code with ruff
	uv run ruff format src/
	uv run ruff check --fix src/

typecheck:  ## Run type checking with mypy
	uv run mypy src/

check: lint typecheck  ## Run all checks (lint + typecheck)

run:  ## Run the dividend tracker
	uv run dividend-tracker

clean:  ## Clean cache and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf dist/ build/ .mypy_cache/

.DEFAULT_GOAL := help
