# Army Markdown Development Makefile

.PHONY: help install install-dev format lint test test-cov clean setup pre-commit security run docker-dev docker-prod

# Default target
help:
	@echo "Army Markdown Development Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install production dependencies with uv"
	@echo "  make install-dev  Install development dependencies with uv"
	@echo "  make setup        Complete development environment setup"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format       Format code with ruff"
	@echo "  make lint         Run linting checks with ruff"
	@echo "  make pre-commit   Run pre-commit hooks on all files"
	@echo "  make security     Run security checks (bandit, safety)"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-cov     Run tests with coverage report"
	@echo "  make test-fast    Run fast tests only (skip slow/integration)"
	@echo ""
	@echo "Development:"
	@echo "  make run          Start Flask development server"
	@echo "  make celery       Start Celery worker"
	@echo "  make redis        Start Redis server (if installed locally)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-dev   Start development environment with Docker"
	@echo "  make docker-prod  Start production environment with Docker"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        Clean up temporary files and caches"
	@echo ""

# Environment setup
install:
	@echo "Installing production dependencies with uv..."
	uv pip install -r requirements.txt

install-dev:
	@echo "Installing development dependencies with uv..."
	uv pip install -r requirements.txt
	uv pip install -r requirements-test.txt

setup: install-dev
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	pre-commit install
	@echo "Development environment ready!"
	@echo "Don't forget to:"
	@echo "1. Edit .env with your actual configuration values"
	@echo "2. Start Redis server: redis-server"
	@echo "3. Run the app: make run"

# Code quality
format:
	@echo "Formatting code with ruff..."
	ruff format .

lint:
	@echo "Running lint checks with ruff..."
	ruff check .

lint-fix:
	@echo "Running lint checks with auto-fix..."
	ruff check . --fix

pre-commit:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

security:
	@echo "Running security checks..."
	bandit -r . -f text || true
	@echo ""
	safety check || true

# Testing
test:
	@echo "Running all tests..."
	pytest

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-fast:
	@echo "Running fast tests only..."
	pytest -m "not slow"

test-verbose:
	@echo "Running tests with verbose output..."
	pytest -v

# Development servers
run:
	@echo "Starting Flask development server..."
	@echo "Make sure Redis is running and .env is configured!"
	flask run --debug

celery:
	@echo "Starting Celery worker..."
	celery -A app.celery worker --loglevel=info

redis:
	@echo "Starting Redis server..."
	redis-server

# Docker commands
docker-dev:
	@echo "Starting development environment with Docker..."
	docker-compose -f docker-compose-dev.yaml up --build

docker-prod:
	@echo "Starting production environment with Docker..."
	docker-compose up --build

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

# Utilities
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".ruff_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -f coverage.xml
	rm -f .coverage
	@echo "Cleanup complete!"

# Development workflow shortcuts
check: lint test
	@echo "All checks passed!"

ci: lint security test-cov
	@echo "CI checks complete!"

# Quick start for new developers
quickstart:
	@echo "Quick start for new developers:"
	@echo "1. Creating virtual environment..."
	uv venv
	@echo "2. Installing dependencies..."
	@$(MAKE) install-dev
	@echo "3. Setting up pre-commit..."
	pre-commit install
	@echo "4. Creating .env file..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "   - Activate virtual environment: source .venv/bin/activate"
	@echo "   - Edit .env with your configuration"
	@echo "   - Start Redis: make redis (in another terminal)"
	@echo "   - Run the app: make run"
