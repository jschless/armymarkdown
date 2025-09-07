"""
Test configuration and fixtures for Army Memo Maker tests.
"""

import os
import shutil
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

from flask import Flask
import pytest

from armymarkdown import memo_model


# Mock the database and login modules before they get imported
def mock_database_modules():
    """Mock database-related modules that may not be available in test environment."""
    # Mock db.schema module
    mock_db_schema = MagicMock()
    mock_db_schema.User = MagicMock()
    mock_db_schema.Document = MagicMock()
    mock_db_schema.db = MagicMock()
    sys.modules["db.schema"] = mock_db_schema
    sys.modules["db"] = MagicMock()
    sys.modules["db.db"] = MagicMock()

    # Create a configurable mock user for current_user first
    mock_user = MagicMock()

    # Mock flask-login components
    mock_flask_login = MagicMock()
    mock_flask_login.LoginManager = MagicMock

    # Mock login_user to actually set session and update user state
    def mock_login_user(user):
        from flask import session

        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.is_anonymous = False
        # Ensure we get actual values, not MagicMock objects
        user_id = getattr(user, "id", 1)
        username = getattr(user, "username", "testuser")
        # Convert MagicMock to actual values if needed
        if hasattr(user_id, "_mock_name"):
            user_id = 1
        if hasattr(username, "_mock_name"):
            username = "testuser"
        mock_user.id = user_id
        mock_user.username = username
        mock_user.get_id.return_value = str(user_id)
        # Also set session for compatibility (use actual values)
        session["user_id"] = user_id
        session["username"] = username
        return True

    def mock_logout_user():
        mock_user.is_authenticated = False
        mock_user.is_active = False
        mock_user.is_anonymous = True
        mock_user.id = None
        mock_user.username = None
        mock_user.get_id.return_value = None
        from flask import session

        session.pop("user_id", None)
        session.pop("username", None)

    mock_flask_login.login_user = mock_login_user
    mock_flask_login.logout_user = mock_logout_user

    # Mock login_required decorator to properly check authentication
    def mock_login_required(f):
        from functools import wraps

        from flask import jsonify, session

        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if user is authenticated (either via mock_user or session)
            # Use try-catch for defensive programming in case of CI environment differences
            try:
                is_authenticated = getattr(mock_user, "is_authenticated", False) or (
                    hasattr(session, "get") and session.get("user_id") is not None
                )
            except Exception:
                # In case session or mock_user is not available, default to not authenticated
                is_authenticated = False

            if not is_authenticated:
                from flask import redirect, request, url_for

                try:
                    # Return 401 for API routes, 302 for HTML routes
                    if request.path.startswith(
                        "/api/"
                    ) or "json" in request.headers.get("Accept", ""):
                        return jsonify({"error": "Authentication required"}), 401
                    else:
                        # For protected routes like /history, return 302 redirect
                        return redirect(url_for("login")), 302
                except Exception:
                    # Fallback: just return 401 if url_for fails
                    return jsonify({"error": "Authentication required"}), 401
            return f(*args, **kwargs)

        return wrapper

    mock_flask_login.login_required = mock_login_required
    mock_user.is_authenticated = False
    mock_user.is_active = False
    mock_user.is_anonymous = True
    mock_user.get_id.return_value = None
    mock_user.id = None
    mock_user.username = None

    # Add method to authenticate user for testing
    def authenticate_test_user(user_id=1, username="testuser"):
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.is_anonymous = False
        mock_user.get_id.return_value = str(user_id)
        mock_user.id = user_id
        mock_user.username = username

    def logout_test_user():
        mock_user.is_authenticated = False
        mock_user.is_active = False
        mock_user.is_anonymous = True
        mock_user.get_id.return_value = None
        mock_user.id = None
        mock_user.username = None

    mock_user.authenticate_for_test = authenticate_test_user
    mock_user.logout_for_test = logout_test_user
    mock_flask_login.current_user = mock_user

    sys.modules["flask_login"] = mock_flask_login

    # Mock Celery to prevent Redis connection attempts
    mock_celery = MagicMock()
    mock_celery_class = MagicMock()

    def task_decorator(f=None, **kwargs):
        """Mock Celery task decorator that adds delay and AsyncResult methods."""

        def decorator(func):
            # Add delay method that returns a mock result
            def delay(*args, **kwargs):
                result = Mock()
                result.id = "test-task-id"
                result.get = Mock(return_value="Mocked task result")
                return result

            # Add AsyncResult method for status checking
            def async_result(task_id):
                result = Mock()
                result.id = task_id
                result.state = "SUCCESS"
                result.result = "Mocked task result"
                result.get = Mock(return_value="Mocked task result")
                return result

            func.delay = delay
            func.AsyncResult = async_result
            return func

        return decorator(f) if f else decorator

    mock_celery_class.task = task_decorator
    mock_celery.Celery = lambda *args, **kwargs: mock_celery_class
    sys.modules["celery"] = mock_celery


# Set up mocks before any imports
mock_database_modules()


@pytest.fixture(scope="session")
def test_app():
    """Create a test Flask application."""
    # Set test environment variables
    test_env = {
        "FLASK_SECRET": "test-secret-key",
        "REDIS_URL": "redis://localhost:6379/15",  # Use test database
        "RECAPTCHA_PUBLIC_KEY": "test-public-key",
        "RECAPTCHA_PRIVATE_KEY": "test-private-key",
        "AWS_ACCESS_KEY_ID": "test-access-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
        "DISABLE_CAPTCHA": "true",
        "DEVELOPMENT": "true",
    }

    with patch.dict(os.environ, test_env):
        try:
            # Import app after setting environment variables and mocks
            from app import app

            app.config["TESTING"] = True
            app.config["WTF_CSRF_ENABLED"] = False
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
            app.config["DISABLE_CAPTCHA"] = True

            # Add current_user to template context for testing
            @app.context_processor
            def inject_user():
                from flask_login import current_user

                return {"current_user": current_user}

            yield app
        except ImportError:
            # If app import fails, create a minimal Flask app for testing
            app = Flask(__name__)
            app.config["TESTING"] = True
            app.config["WTF_CSRF_ENABLED"] = False
            app.config["SECRET_KEY"] = "test-secret-key"
            app.config["DISABLE_CAPTCHA"] = True
            yield app


@pytest.fixture
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()


@pytest.fixture
def app_context(test_app):
    """Create an application context for the test."""
    with test_app.app_context():
        yield test_app


@pytest.fixture
def auth_user():
    """Fixture to control user authentication in tests with proper isolation."""
    from flask_login import current_user

    class AuthController:
        def __init__(self):
            # Store original state to restore later
            self.original_authenticated = getattr(
                current_user, "is_authenticated", False
            )
            self.original_active = getattr(current_user, "is_active", False)
            self.original_anonymous = getattr(current_user, "is_anonymous", True)
            self.original_id = getattr(current_user, "id", None)
            self.original_username = getattr(current_user, "username", None)

        def login(self, user_id=1, username="testuser"):
            current_user.authenticate_for_test(user_id, username)

        def logout(self):
            current_user.logout_for_test()

        def restore_original_state(self):
            # Restore the original state
            current_user.is_authenticated = self.original_authenticated
            current_user.is_active = self.original_active
            current_user.is_anonymous = self.original_anonymous
            current_user.id = self.original_id
            current_user.username = self.original_username
            if hasattr(current_user, "get_id"):
                current_user.get_id.return_value = (
                    str(self.original_id) if self.original_id else None
                )

    controller = AuthController()
    # Start with logged out user
    controller.logout()

    try:
        yield controller
    finally:
        # Always restore original state after test, regardless of what happened
        controller.restore_original_state()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_memo_dict():
    """Sample memo data as a dictionary with all required fields."""
    return {
        "unit_name": "4th Engineer Battalion",
        "unit_street_address": "588 Wetzel Road",
        "unit_city_state_zip": "Colorado Springs, CO 80904",
        "office_symbol": "ABC-DEF-GH",
        "subject": "Test Memo Subject",
        "text": [
            "This is a test memo.",
            "This item contains sub items:",
            ["First sub-item", "Second sub-item", ["Nested sub-item"]],
            "Point of contact is the undersigned.",
        ],
        "author_name": "John A. Smith",
        "author_rank": "CPT",
        "author_branch": "EN",
        "author_title": "Company Commander",
        "memo_type": "MEMORANDUM FOR RECORD",
        "todays_date": "15 March 2024",
    }


@pytest.fixture
def sample_memo_text():
    """Sample memo in Army Markdown format."""
    return """ORGANIZATION_NAME=4th Engineer Battalion
ORGANIZATION_STREET_ADDRESS=588 Wetzel Road
ORGANIZATION_CITY_STATE_ZIP=Colorado Springs, CO 80904

OFFICE_SYMBOL=ABC-DEF-GH
DATE=15 March 2024
AUTHOR=John A. Smith
RANK=CPT
BRANCH=EN
TITLE=Company Commander

SUBJECT=Test Memo Subject

- This is a test memo.

- This item contains sub items:
    - First sub-item
    - Second sub-item
        - Nested sub-item

- Point of contact is the undersigned.
"""


@pytest.fixture
def sample_form_data():
    """Sample form data for testing form processing."""
    return {
        "ORGANIZATION_NAME": "4th Engineer Battalion",
        "ORGANIZATION_STREET_ADDRESS": "588 Wetzel Road",
        "ORGANIZATION_CITY_STATE_ZIP": "Colorado Springs, CO 80904",
        "OFFICE_SYMBOL": "ABC-DEF-GH",
        "DATE": "15 March 2024",
        "AUTHOR": "John A. Smith",
        "RANK": "CPT",
        "BRANCH": "EN",
        "TITLE": "Company Commander",
        "SUBJECT": "Test Memo Subject",
        "MEMO_TEXT": "- This is a test memo.\n\n- Point of contact is the undersigned.",
    }


@pytest.fixture
def invalid_memo_samples():
    """Collection of invalid memo samples for error testing."""
    return {
        "missing_subject": """ORGANIZATION_NAME=Test Unit
AUTHOR=John Smith
RANK=CPT
BRANCH=EN

- This memo has no subject.""",
        "invalid_date": """ORGANIZATION_NAME=Test Unit
AUTHOR=John Smith
RANK=CPT
BRANCH=EN
DATE=Invalid Date Format

SUBJECT=Test Subject

- This memo has an invalid date.""",
        "invalid_branch": """ORGANIZATION_NAME=Test Unit
AUTHOR=John Smith
RANK=CPT
BRANCH=INVALID
DATE=15 March 2024

SUBJECT=Test Subject

- This memo has an invalid branch.""",
        "missing_required_fields": """SUBJECT=Test Subject

- This memo is missing required fields.""",
    }


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing file operations."""
    with patch("boto3.client") as mock_client:
        mock_s3 = Mock()
        mock_client.return_value = mock_s3
        yield mock_s3


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing background operations."""
    with patch("app.create_memo.delay") as mock_task:
        mock_result = Mock()
        mock_result.id = "test-task-id"
        mock_task.return_value = mock_result
        yield mock_task


@pytest.fixture
def test_database(temp_dir):
    """Create a test SQLite database."""
    db_path = os.path.join(temp_dir, "test.db")
    conn = sqlite3.connect(db_path)

    # Create test tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup is handled by temp_dir fixture


@pytest.fixture
def special_characters_samples():
    """Sample text with special characters for LaTeX escaping tests."""
    return {
        "latex_special": "Text with & % $ # _ { } characters",
        "markdown_formatting": "**Bold text** and *italic text* and `code text`",
        "mixed_content": "Company & **Organization** costs $1000 {special} 50% done #1 priority_item",
        "unicode_chars": "Café résumé naïve 中文 español",
        "symbols": "~tilde ^caret \\backslash @ copyright © trademark ™",
    }
