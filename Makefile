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
	@echo "  make docker-dev       Start development environment with Docker (Ctrl+C to stop)"
	@echo "  make docker-dev-build Build and start development environment with Docker"
	@echo "  make docker-prod      Start production environment with Docker"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        Clean up temporary files and caches"
	@echo ""

# Environment setup
install:
	@echo "Installing production dependencies with uv..."
	uv sync --no-dev

install-dev:
	@echo "Installing development dependencies with uv..."
	uv sync

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
	uv run ruff format .

lint:
	@echo "Running lint checks with ruff..."
	uv run ruff check .

lint-fix:
	@echo "Running lint checks with auto-fix..."
	uv run ruff check . --fix

pre-commit:
	@echo "Running pre-commit hooks..."
	uv run pre-commit run --all-files

security:
	@echo "Running security checks..."
	uv run bandit -r . -f text || true
	@echo ""
	uv run safety check || true

# Testing
test:
	@echo "Running all tests (excluding selenium)..."
	PYTHONPATH=. uv run pytest --ignore=tests/test_pdf_generation_e2e.py --ignore=tests/test_selenium_e2e.py --ignore=tests/test_ui_selenium.py

test-cov:
	@echo "Running tests with coverage..."
	PYTHONPATH=. uv run pytest --cov=. --cov-report=html --cov-report=term-missing --ignore=tests/test_pdf_generation_e2e.py --ignore=tests/test_selenium_e2e.py --ignore=tests/test_ui_selenium.py

test-fast:
	@echo "Running fast tests only..."
	PYTHONPATH=. uv run pytest -m "not slow" --ignore=tests/test_pdf_generation_e2e.py --ignore=tests/test_selenium_e2e.py --ignore=tests/test_ui_selenium.py

test-verbose:
	@echo "Running tests with verbose output..."
	PYTHONPATH=. uv run pytest -v --ignore=tests/test_pdf_generation_e2e.py --ignore=tests/test_selenium_e2e.py --ignore=tests/test_ui_selenium.py

test-all:
	@echo "Running ALL tests (including selenium - requires selenium to be installed)..."
	PYTHONPATH=. uv run pytest -v

# Development servers
run:
	@echo "Starting Flask development server..."
	@echo "Make sure Redis is running and .env is configured!"
	FLASK_APP=app.main uv run flask run --debug

celery:
	@echo "Starting Celery worker..."
	uv run celery -A app.main.celery worker --loglevel=info

redis:
	@echo "Starting Redis server..."
	redis-server

# Docker commands
docker-dev:
	@echo "Starting development environment with Docker..."
	@echo "Press Ctrl+C to stop all services"
	docker compose -f infrastructure/compose/docker-compose-dev.yaml up

docker-dev-build:
	@echo "Building and starting development environment with Docker..."
	@echo "Press Ctrl+C to stop all services"
	docker compose -f infrastructure/compose/docker-compose-dev.yaml up --build

docker-prod:
	@echo "Starting production environment with Docker..."
	docker compose -f infrastructure/compose/docker-compose.yaml up --build

docker-stop:
	@echo "Stopping Docker containers..."
	docker compose down

# Utilities
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".ruff_cache" -delete
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
	@echo "1. Creating virtual environment and installing dependencies..."
	uv sync
	@echo "2. Setting up pre-commit..."
	uv run pre-commit install
	@echo "3. Creating .env file..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "   - Edit .env with your configuration"
	@echo "   - Start Redis: make redis (in another terminal)"
	@echo "   - Run the app: make run"
