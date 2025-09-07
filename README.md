# Army Memo Maker

[![Deploy to DigitalOcean](https://github.com/jschless/armymarkdown/actions/workflows/deploy.yml/badge.svg)](https://github.com/jschless/armymarkdown/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> A modern web application for creating professional Army memorandums in perfect accordance with AR 25-50. Fast, secure, and DoD network compatible.

🌐 **Live Application:** [armymemomaker.com](https://www.armymemomaker.com)

## ✨ Features

### 🎯 **Core Functionality**
- **Professional memo generation** - LaTeX-powered formatting ensures AR 25-50 compliance
- **Dual input modes** - Choose between markdown-like syntax or guided form builder
- **Real-time compilation** - PDFs generated on-demand with optimized LaTeX processing
- **Document management** - Save, edit, and organize your memos with user accounts

### 🎨 **Modern Interface**
- **Dark/Light mode** - Toggle between themes with persistent preferences
- **Responsive design** - Works seamlessly on desktop and mobile devices
- **Clean typography** - Professional appearance with modern fonts and spacing
- **Accessibility focused** - Built with inclusive design principles

### 🔒 **Security & Reliability**
- **SSL/TLS encryption** - End-to-end security with Let's Encrypt certificates
- **User authentication** - Secure account system with password hashing
- **Input validation** - Comprehensive sanitization and validation
- **CAPTCHA protection** - Spam prevention (configurable for testing environments)

### ⚡ **Performance & Modern Tooling**
- **Asynchronous processing** - Background PDF generation with Celery workers
- **Fast dependency management** - uv package manager with lockfile support
- **Optimized LaTeX** - Single-pass compilation for faster document creation
- **Modern Python packaging** - pyproject.toml with standardized build system
- **AWS S3 integration** - Reliable file storage and delivery
- **Docker containerization** - Consistent deployment across environments

## 🚀 Quick Start

### Prerequisites

- **Docker and Docker Compose** - For containerized development
- **Git** - Version control
- **uv** (optional) - For local Python development: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Development Setup

#### Option 1: Docker Development (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/jschless/armymarkdown.git
   cd armymarkdown
   ```

2. **Set up environment variables**
   ```bash
   # Create environment file with required settings
   export FLASK_SECRET="your-development-secret-key"
   export REDIS_URL="redis://redis:6379/0"
   export DISABLE_CAPTCHA="true"  # For development
   export DEVELOPMENT="true"
   ```

3. **Start development environment**
   ```bash
   docker-compose -f docker-compose-dev.yaml up --build
   ```

4. **Access the application**
   - Web interface: http://localhost:8000
   - The application will hot-reload when you make changes

#### Option 2: Local Python Development

1. **Install dependencies with uv**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv sync --extra dev
   ```

2. **Set up environment variables**
   ```bash
   export FLASK_SECRET="dev-secret-key"
   export REDIS_URL="redis://localhost:6379/15"
   export DISABLE_CAPTCHA="true"
   export DEVELOPMENT="true"
   ```

3. **Run the application**
   ```bash
   # Start Redis (if not using Docker)
   redis-server

   # Start the Flask app
   uv run python app.py
   ```

### Production Deployment

1. **Configure environment variables on your server**
   ```bash
   export FLASK_SECRET="your-secret-key"
   export REDIS_URL="redis://redis:6379/0"
   export RECAPTCHA_PUBLIC_KEY="your-public-key"
   export RECAPTCHA_PRIVATE_KEY="your-private-key"
   export AWS_ACCESS_KEY_ID="your-aws-key"
   export AWS_SECRET_ACCESS_KEY="your-aws-secret"
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose up --build -d
   ```

3. **Optional: Disable CAPTCHA for testing**
   ```bash
   export DISABLE_CAPTCHA=true
   ```

## 📝 Army Markdown Syntax

Create professional memos using our intuitive markdown-like syntax:

```markdown
ORGANIZATION_NAME=4th Engineer Battalion
ORGANIZATION_STREET_ADDRESS=588 Wetzel Road
ORGANIZATION_CITY_STATE_ZIP=Colorado Springs, CO 80904

OFFICE_SYMBOL=ABC-DEF-GH
AUTHOR=Joseph C. Schlessinger
RANK=1LT
BRANCH=EN
TITLE=Platoon Leader

MEMO_TYPE=MEMORANDUM FOR RECORD
SUBJECT=Template for Army Markdown

- This memo demonstrates the Army Markdown syntax.

- This item contains sub items:
    - A subitem is created by indenting 4 spaces
    - A second subitem within the same point
        - Here is a sub-sub item

- **Bold text**, *italic text*, and `highlighted text` are supported.

- Point of contact is the undersigned at (719) 555-0123.
```

### Supported Features

- **Text formatting**: Bold, italic, and highlighted text
- **Nested lists**: Multi-level indentation with automatic formatting
- **Tables**: Basic table support for structured data
- **Classifications**: Support for classified document markings
- **Enclosures**: Automatic enclosure numbering and references

## 🏗️ Architecture

### Technology Stack

- **Backend**: Python Flask with Gunicorn WSGI server
- **Package Management**: uv for fast, reliable dependency resolution
- **Build System**: Modern Python packaging with pyproject.toml
- **Task Queue**: Celery with Redis for asynchronous PDF generation
- **Database**: SQLite for user accounts and document storage
- **PDF Generation**: LuaLaTeX with custom Army memo class
- **Frontend**: Modern CSS with vanilla JavaScript
- **Containerization**: Docker with multi-stage builds
- **Reverse Proxy**: Nginx with SSL termination

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│   Flask App     │────│   Celery Worker │
│   (Port 80/443) │    │   (Port 8000)   │    │   (Background)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Redis Queue   │    │   SQLite DB     │
                    │   (Port 6379)   │    │   (Volume)      │
                    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FLASK_SECRET` | Flask session secret key | ✅ | - |
| `REDIS_URL` | Redis connection URL | ✅ | - |
| `RECAPTCHA_PUBLIC_KEY` | reCAPTCHA site key | ✅ | - |
| `RECAPTCHA_PRIVATE_KEY` | reCAPTCHA secret key | ✅ | - |
| `AWS_ACCESS_KEY_ID` | AWS S3 access key | ✅ | - |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key | ✅ | - |
| `DISABLE_CAPTCHA` | Disable CAPTCHA for testing | ❌ | `false` |
| `DEVELOPMENT` | Enable development mode | ❌ | `false` |

### Security Configuration

The application includes several security measures:

- **Content Security Policy (CSP)** with restricted script sources
- **SSL/TLS encryption** with automatic certificate renewal
- **Input sanitization** and validation on all user inputs
- **Rate limiting** and CAPTCHA protection against abuse
- **Secure session management** with httpOnly cookies

## 🧪 Testing

### Running Tests with uv

```bash
# Run all tests with coverage
uv run pytest tests/ --cov=. --cov-report=term-missing

# Run specific test categories
uv run pytest tests/test_input_validation.py -v
uv run pytest tests/test_latex_escape_chars.py -v

# Run tests matching a pattern
uv run pytest tests/ -k "test_memo" -v

# Run Selenium end-to-end tests (requires running server)
uv run pytest tests/ -m selenium -v

# Run all tests except slow/selenium tests
uv run pytest tests/ -m "not slow and not selenium" -v
```

### Docker Testing Environment

```bash
# Run tests in Docker container
docker-compose -f docker-compose-dev.yaml exec flask_app uv run pytest tests/

# Or build and run tests in isolated container
docker build -f Dockerfile.development -t armymarkdown-test .
docker run --rm armymarkdown-test uv run pytest tests/ --tb=short
```

### Test Environment Variables

The tests require these environment variables:

```bash
export FLASK_SECRET="test-secret-key-for-ci"
export REDIS_URL="redis://localhost:6379/15"
export RECAPTCHA_PUBLIC_KEY="test-public-key"
export RECAPTCHA_PRIVATE_KEY="test-private-key"
export AWS_ACCESS_KEY_ID="test-access-key"
export AWS_SECRET_ACCESS_KEY="test-secret-key"
export DISABLE_CAPTCHA="true"
export DEVELOPMENT="true"
```

## 📚 API Documentation

### Endpoints

- `GET /` - Main memo editor interface
- `GET /form` - Form-based memo builder
- `GET /history` - User's saved documents (requires authentication)
- `POST /process` - Submit memo for PDF generation
- `POST /save_progress` - Save draft (requires authentication)
- `GET /status/<task_id>` - Check PDF generation status

### Authentication

- `GET /login` - User login page
- `POST /login` - Process login credentials
- `GET /register` - User registration page
- `POST /register` - Create new user account
- `GET /logout` - End user session

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/armymarkdown.git
   cd armymarkdown
   ```

2. **Set up development environment**
   ```bash
   # Install uv if needed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync --extra dev
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make your changes with tests**
   ```bash
   # Run tests frequently during development
   uv run pytest tests/ -v

   # Check code quality
   uv run ruff check .
   uv run ruff format .
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request** with a clear description of your changes

### Code Standards

- **Python**: Follow PEP 8, use type hints where helpful
- **Code Quality**: Use `ruff` for linting and formatting
- **Testing**: Write tests for new functionality (`pytest`)
- **Dependencies**: Use `uv add` for new dependencies
- **Documentation**: Update README and docstrings as needed
- **Docker**: Ensure both development and production builds succeed

### Quality Checks

Before submitting a PR, ensure these pass:

```bash
# Code formatting and linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy . --ignore-missing-imports

# Security scanning
uv run bandit -r . -x tests/
uv run safety check

# Full test suite with coverage
PYTHONPATH=. uv run pytest tests/ --cov=. --cov-report=term-missing
```

### Development Tools & Configuration

The project uses modern Python tooling for development:

- **`pyproject.toml`** - Centralized project configuration
- **`uv.lock`** - Locked dependency versions for reproducible builds
- **`ruff`** - Fast Python linter and formatter (replaces flake8, black, isort)
- **`mypy`** - Static type checking
- **`bandit`** - Security vulnerability scanning
- **`safety`** - Dependency vulnerability checking
- **`pytest`** - Testing framework with coverage reporting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [army-memorandum-class](https://github.com/glallen01/army-memorandum-class) - LaTeX class for Army memos
- [LaTeX Project](https://www.latex-project.org/) - Document preparation system
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Celery](https://docs.celeryproject.org/) - Distributed task queue

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jschless/armymarkdown/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jschless/armymarkdown/discussions)
- **Email**: [Contact the maintainer](mailto:joe.c.schlessinger@gmail.com)

---

<div align="center">

**Built with ❤️ for the United States Army**

[⭐ Star this repo](https://github.com/jschless/armymarkdown) • [🐛 Report Bug](https://github.com/jschless/armymarkdown/issues) • [✨ Request Feature](https://github.com/jschless/armymarkdown/issues)

</div>
