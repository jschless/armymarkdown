"""
Test configuration and fixtures for Army Memo Maker tests.
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch
from flask import Flask
from armymarkdown import memo_model
import sqlite3


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
        # Import app after setting environment variables
        from app import app
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
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
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_memo_dict():
    """Sample memo data as a dictionary."""
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