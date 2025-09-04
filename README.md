# Army Memo Maker

[![Deploy to DigitalOcean](https://github.com/jschless/armymarkdown/actions/workflows/deploy.yml/badge.svg)](https://github.com/jschless/armymarkdown/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

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

### ⚡ **Performance**
- **Asynchronous processing** - Background PDF generation with Celery workers
- **Optimized LaTeX** - Single-pass compilation for faster document creation
- **AWS S3 integration** - Reliable file storage and delivery
- **Docker containerization** - Consistent deployment across environments

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jschless/armymarkdown.git
   cd armymarkdown
   ```

2. **Set up environment variables**
   ```bash
   cp local_config.example.py local_config.py
   # Edit local_config.py with your configuration
   ```

3. **Start development environment**
   ```bash
   docker-compose -f docker-compose-dev.yaml up --build
   ```

4. **Access the application**
   - Web interface: http://localhost:8000
   - The application will hot-reload when you make changes

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

Run the test suite to ensure everything works correctly:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_input_validation.py
python -m pytest tests/test_latex_escape_chars.py
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

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Write tests for new functionality
- Update documentation as needed
- Ensure Docker builds succeed

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