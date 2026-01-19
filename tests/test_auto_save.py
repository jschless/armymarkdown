"""Tests for auto-save functionality"""

import json
from unittest.mock import Mock, patch

import pytest

from app.main import app


@pytest.fixture
def client():
    """Create a test client"""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["DISABLE_CAPTCHA"] = True

    with app.test_client() as client:
        yield client


class TestAutoSave:
    """Test auto-save functionality"""

    @patch("flask_login.utils._get_user")
    @patch("app.auth.login.auto_save_document")
    def test_auto_save_text_editor_mode(
        self, mock_auto_save, mock_current_user, client
    ):
        """Test auto-save for text editor mode"""
        # Mock authenticated user
        mock_current_user.return_value = Mock(is_authenticated=True, id=1)
        mock_auto_save.return_value = {
            "success": True,
            "message": "Draft auto-saved",
            "action": "saved",
            "removed_oldest": False,
        }

        memo_text = "MEMORANDUM FOR RECORD\n\nSUBJECT: Test Auto-save\n\n1. This is a test memo for auto-save functionality."

        response = client.post(
            "/auto_save",
            data={"memo_text": memo_text},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["action"] == "saved"
        assert "timestamp" in data

    @patch("flask_login.utils._get_user")
    @patch("app.auth.login.auto_save_document")
    def test_auto_save_duplicate_content(
        self, mock_auto_save, mock_current_user, client
    ):
        """Test auto-save handles duplicate content gracefully"""
        # Mock authenticated user
        mock_current_user.return_value = Mock(is_authenticated=True, id=1)
        mock_auto_save.return_value = {
            "success": True,
            "message": "No changes to save",
            "action": "skipped",
            "reason": "identical_content",
        }

        memo_text = "MEMORANDUM FOR RECORD\n\nSUBJECT: Test Duplicate\n\n1. This content already exists."

        response = client.post(
            "/auto_save",
            data={"memo_text": memo_text},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["action"] == "skipped"
        assert data["message"] == "No changes to save"
        assert "timestamp" in data

    @patch("flask_login.utils._get_user")
    @patch("app.auth.login.auto_save_document")
    def test_auto_save_form_mode(self, mock_auto_save, mock_current_user, client):
        """Test auto-save for form mode"""
        # Mock authenticated user
        mock_current_user.return_value = Mock(is_authenticated=True, id=1)
        mock_auto_save.return_value = {
            "success": True,
            "message": "Draft auto-saved",
            "action": "saved",
            "removed_oldest": False,
        }

        form_data = {
            "ORGANIZATION_NAME": "36th Engineer Brigade",
            "ORGANIZATION_STREET_ADDRESS": "1234 Washington Road",
            "ORGANIZATION_CITY_STATE_ZIP": "Fort Cavazos, TX 01234",
            "OFFICE_SYMBOL": "ABC-DEF-GHIJ",
            "DATE": "24 January 2006",
            "SUBJECT": "Test Auto-save Form Mode",
            "MEMO_TEXT": "1. This is a test memo from form mode.\n\n2. Testing auto-save functionality.",
            "AUTHOR": "John Doe",
            "RANK": "CPT",
            "BRANCH": "EN",
        }

        response = client.post(
            "/auto_save", data=form_data, headers={"X-Requested-With": "XMLHttpRequest"}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["action"] == "saved"
        assert "timestamp" in data

    @patch("flask_login.utils._get_user")
    def test_auto_save_empty_content(self, mock_current_user, client):
        """Test auto-save with empty content"""
        # Mock authenticated user
        mock_current_user.return_value = Mock(is_authenticated=True, id=1)

        response = client.post(
            "/auto_save",
            data={"memo_text": ""},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "No content to save" in data["error"]

    @patch("flask_login.utils._get_user")
    def test_auto_save_whitespace_only(self, mock_current_user, client):
        """Test auto-save with whitespace-only content"""
        # Mock authenticated user
        mock_current_user.return_value = Mock(is_authenticated=True, id=1)

        response = client.post(
            "/auto_save",
            data={"memo_text": "   \n  \t  \n  "},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "No content to save" in data["error"]

    def test_auto_save_requires_authentication(self, client):
        """Test that auto-save requires authentication"""
        response = client.post(
            "/auto_save",
            data={"memo_text": "Test memo content"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        # Should redirect to login (302) or return unauthorized (401)
        assert response.status_code in [302, 401]

    @patch("flask_login.utils._get_user")
    def test_auto_save_invalid_form_data(self, mock_current_user, client):
        """Test auto-save with invalid form data"""
        # Mock authenticated user
        mock_current_user.return_value = Mock(is_authenticated=True, id=1)

        # Missing required form fields
        form_data = {
            "SUBJECT": "Test Subject",
            "MEMO_TEXT": "Test content",
            # Missing ORGANIZATION_NAME and other required fields
        }

        response = client.post(
            "/auto_save", data=form_data, headers={"X-Requested-With": "XMLHttpRequest"}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Error creating memo" in data["error"]

    @patch("flask_login.utils._get_user")
    @patch("app.auth.login.save_document")
    def test_auto_save_returns_json(
        self, mock_save_document, mock_current_user, client
    ):
        """Test that auto-save returns proper JSON response"""
        # Mock authenticated user
        mock_current_user.return_value = Mock(is_authenticated=True, id=1)
        mock_save_document.return_value = None  # No error

        response = client.post(
            "/auto_save",
            data={"memo_text": "Test memo content"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        assert response.status_code == 200
        assert response.content_type == "application/json"

        # Verify it's valid JSON
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert "success" in data
        assert "message" in data
        assert "timestamp" in data
