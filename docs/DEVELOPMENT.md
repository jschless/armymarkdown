# Development Guide

This document contains comprehensive information for developers working on the Army Markdown project.

## Quick Start

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) for fast Python package management
- Redis (for Celery task queue)
- LaTeX distribution (for PDF generation)

### Setup with uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/jschless/armymarkdown.git
cd armymarkdown

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install -r requirements-test.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# Install pre-commit hooks
pre-commit install

# Run the application
flask run
```

### Alternative Setup with pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Continue with environment setup as above
```

## Development Workflow

### Code Quality

We use **ruff** for both linting and code formatting, replacing multiple tools with a single, fast solution:

```bash
# Check code quality
ruff check .

# Fix auto-fixable issues
ruff check . --fix

# Format code
ruff format .

# Check formatting without making changes
ruff format --check .
```

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit:

```bash
# Install hooks (one-time setup)
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Update hook repositories
pre-commit autoupdate
```

Our pre-commit configuration includes:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Bandit** for security linting
- **Safety** for vulnerability checking
- Basic file checks (trailing whitespace, merge conflicts, etc.)

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_specific.py

# Run tests with verbose output
pytest -v

# Run only fast tests (skip slow/integration tests)
pytest -m "not slow"
```

### Type Checking

```bash
# Run MyPy type checking
mypy --ignore-missing-imports armymarkdown/

# Check specific files
mypy armymarkdown/memo_model.py
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
├── armymarkdown/           # Main application package
│   ├── __init__.py
│   ├── memo_model.py      # Core memo parsing logic
│   └── writer.py          # LaTeX generation
├── templates/             # Jinja2 templates
├── static/               # CSS, JS, and static assets
├── tests/               # Test suite
├── latex/              # LaTeX class files
├── examples/           # Example memo files (.Amd)
├── .github/workflows/  # CI/CD configuration
├── app.py             # Flask application entry point
├── forms.py           # WTForms definitions
├── login.py           # Authentication logic
├── pyproject.toml     # Project configuration
├── requirements.txt   # Production dependencies
├── requirements-test.txt  # Development dependencies
└── .env.example       # Environment variables template
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Flask Configuration
FLASK_SECRET=your-very-secure-flask-secret-key-here

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0

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
- **MyPy** type checking settings
- **Pytest** test configuration
- **Coverage** reporting settings
- **Bandit** security scanning

## Available Commands

### Development Server

```bash
# Run Flask development server
flask run

# Run with debug mode
FLASK_DEBUG=1 flask run

# Run on specific host/port
flask run --host=0.0.0.0 --port=8000
```

### Background Tasks

```bash
# Start Celery worker (in separate terminal)
celery -A app.celery worker --loglevel=info

# Start Celery flower monitoring (optional)
celery -A app.celery flower
```

### Database Operations

```bash
# Initialize database
flask db init

# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
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

2. **Redis connection errors**
   - Ensure Redis is running: `redis-server`
   - Check REDIS_URL in environment

3. **Import errors**
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
- Redis server running
- LaTeX installation available
- Proper file permissions for uploads

### Docker

Use the provided Docker configuration:
```bash
# Development
docker-compose -f docker-compose-dev.yaml up

# Production
docker-compose up
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Documentation](https://pre-commit.com/)
