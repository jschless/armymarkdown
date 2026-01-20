# Development Guide

This document contains comprehensive information for developers working on the Army Markdown project.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for fast Python package management
- Docker and Docker Compose (recommended for development)
- LaTeX distribution (for PDF generation, included in Docker)

### Docker Development (Recommended)

```bash
# Clone the repository
git clone https://github.com/jschless/armymarkdown.git
cd armymarkdown

# Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# Start development environment
make docker-dev-build
```

### Local Development with uv

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/jschless/armymarkdown.git
cd armymarkdown

# Create virtual environment and install dependencies
uv sync --extra dev

# Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# Install pre-commit hooks
uv run pre-commit install

# Run the application
make run
```

## Available Make Commands

The project includes a comprehensive Makefile with common development tasks:

```bash
# Development
make run          # Start Flask development server
make huey         # Start Huey task consumer

# Docker
make docker-dev        # Start development environment
make docker-dev-build  # Build and start development environment
make docker-prod       # Start production environment

# Code Quality
make format       # Format code with ruff
make lint         # Run linting checks
make pre-commit   # Run pre-commit hooks

# Testing
make test         # Run all tests (excluding selenium)
make test-cov     # Run tests with coverage
make test-fast    # Run fast tests only
make test-verbose # Run tests with verbose output

# Utilities
make clean        # Clean up temporary files
make setup        # Complete development environment setup
```

## Development Workflow

### Code Quality

We use **ruff** for both linting and code formatting, replacing multiple tools with a single, fast solution:

```bash
# Check code quality
make lint

# Fix auto-fixable issues
make lint-fix

# Format code
make format

# Run all quality checks
make check
```

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit:

```bash
# Install hooks (one-time setup)
make setup

# Run hooks manually on all files
make pre-commit

# Update hook repositories
uv run pre-commit autoupdate
```

Our pre-commit configuration includes:
- **Ruff** for linting and formatting
- **Bandit** for security linting
- **Safety** for vulnerability checking
- Basic file checks (trailing whitespace, merge conflicts, etc.)

### Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
PYTHONPATH=. uv run pytest tests/test_specific.py

# Run tests with verbose output
make test-verbose

# Run only fast tests (skip slow/integration tests)
make test-fast
```


### Security Scanning

```bash
# Check for known vulnerabilities
safety check

# Security linting
bandit -r .

# Both are included in pre-commit hooks
```

## Project Structure

```
armymarkdown/
├── app/                   # Main application package
│   ├── auth/             # Authentication modules
│   ├── models/           # Data models
│   ├── services/         # Business logic services
│   ├── main.py          # Flask application entry point
│   └── forms.py         # WTForms definitions
├── db/                   # Database modules
│   ├── schema.py        # SQLAlchemy models
│   └── db.py           # Database initialization
├── infrastructure/      # Docker and deployment config
│   ├── compose/         # Docker Compose files
│   └── docker/          # Dockerfiles
├── resources/           # LaTeX class files and assets
│   └── latex/          # LaTeX templates and styles
├── templates/           # Jinja2 templates
├── static/             # CSS, JS, and static assets
├── tests/              # Test suite
├── docs/               # Documentation
├── .github/workflows/  # CI/CD configuration
├── pyproject.toml      # Project configuration
├── uv.lock            # Locked dependencies
├── Makefile           # Development commands
└── .env.example       # Environment variables template
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Flask Configuration
FLASK_SECRET=your-very-secure-flask-secret-key-here

# reCAPTCHA Configuration
RECAPTCHA_PUBLIC_KEY=your-recaptcha-public-key
RECAPTCHA_PRIVATE_KEY=your-recaptcha-private-key

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key

# Development Options
DISABLE_CAPTCHA=true
DEVELOPMENT=true
```

### pyproject.toml

The `pyproject.toml` file contains configuration for:
- **Project metadata** and dependencies
- **Ruff** linting and formatting rules
- **Pytest** test configuration
- **Coverage** reporting settings
- **Bandit** security scanning

## Available Commands

### Development Server

```bash
# Run Flask development server
make run

# Run with Docker
make docker-dev

# Start background task consumer (optional, in separate terminal)
make huey
```

### Database Operations

The application uses SQLite with automatic migration handling:

```bash
# Database initialization happens automatically on app startup
# Check logs to verify database creation

# For manual database operations (if needed):
# SQLite database is stored in /data/users.db (in Docker)
```

## Code Style Guidelines

### Ruff Configuration

Our Ruff setup enforces:
- **Line length**: 88 characters (Black-compatible)
- **Import sorting**: isort-compatible
- **Code quality**: pycodestyle, Pyflakes, and additional rules
- **Modern Python**: pyupgrade for syntax modernization

### Key Rules

- Use double quotes for strings
- 4-space indentation
- Follow PEP 8 naming conventions
- Prefer f-strings over `.format()` or `%` formatting
- Use type hints where appropriate
- Keep functions focused and small

### Ignored Rules

We selectively ignore some rules:
- `E501`: Line too long (handled by formatter)
- `B008`: Function calls in defaults (for Flask routes)
- `N806`: Lowercase variables (compatibility with existing code)

## Testing Guidelines

### Test Structure

- **Unit tests**: Fast, isolated tests in `tests/test_*.py`
- **Integration tests**: End-to-end tests in `tests/test_integration.py`
- **Fixtures**: Shared test data in `tests/conftest.py`

### Test Naming

- Test files: `test_<module_name>.py`
- Test classes: `TestClassName`
- Test methods: `test_specific_behavior`

### Markers

Use pytest markers for test organization:
```python
@pytest.mark.slow
def test_expensive_operation():
    pass

@pytest.mark.integration
def test_full_workflow():
    pass
```

## Debugging

### Common Issues

1. **LaTeX compilation fails**
   - Check LaTeX installation
   - Verify file paths in logs
   - Check timeout settings

2. **Import errors**
   - Verify PYTHONPATH is set correctly
   - Check virtual environment activation

### Logging

Add logging for debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### Flask Debug Mode

Enable Flask debug mode for development:
```bash
export FLASK_DEBUG=1
flask run
```

## Contributing

### Pull Request Process

1. Create a feature branch: `git checkout -b feature/description`
2. Make changes and add tests
3. Run quality checks: `pre-commit run --all-files`
4. Commit changes: `git commit -m "Description"`
5. Push and create pull request

### Commit Messages

Use clear, descriptive commit messages:
- `feat: add new memo template support`
- `fix: resolve LaTeX timeout issue`
- `docs: update development guide`
- `test: add integration tests for forms`

### Code Review Checklist

- [ ] Tests pass locally and in CI
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] Security considerations addressed
- [ ] Performance impact considered

## Deployment

### Environment Setup

Production deployment requires:
- Environment variables properly configured
- LaTeX installation available
- Proper file permissions for uploads

### Docker

Use the provided Docker configuration:
```bash
# Development
make docker-dev-build

# Production
make docker-prod

# Manual Docker commands:
# docker compose -f infrastructure/compose/docker-compose-dev.yaml up --build
# docker compose -f infrastructure/compose/docker-compose.yaml up --build
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Documentation](https://pre-commit.com/)
