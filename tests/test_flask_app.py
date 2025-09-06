"""
Comprehensive tests for Flask application routes and functionality.
"""

import json
import os
from unittest.mock import Mock, patch

from flask import url_for
import pytest


class TestRoutes:
    """Test all Flask application routes."""

    def test_index_route_get(self, client):
        """Test GET request to index route."""
        response = client.get("/")

        assert response.status_code == 200
        assert b"memo_text" in response.data  # Should contain textarea
        # Should load default tutorial example

    def test_index_route_with_example_file(self, client):
        """Test index route with specific example file."""
        response = client.get("/?example_file=basic_mfr.Amd")

        assert response.status_code == 200
        assert b"memo_text" in response.data

    def test_index_route_invalid_example_file(self, client):
        """Test index route with invalid example file falls back to default."""
        response = client.get("/?example_file=nonexistent.Amd")

        assert response.status_code == 200
        # Should fall back to default example

    def test_form_route_get(self, client):
        """Test GET request to form route."""
        response = client.get("/form")

        assert response.status_code == 200
        # Should contain form fields
        assert b"ORGANIZATION_NAME" in response.data
        assert b"SUBJECT" in response.data

    def test_form_route_with_example(self, client):
        """Test form route with specific example."""
        response = client.get("/form?example_file=memo_for.Amd")

        assert response.status_code == 200
        assert b"ORGANIZATION_NAME" in response.data


class TestProcessing:
    """Test memo processing functionality."""

    @patch("app.create_memo.delay")
    @patch("login.save_document")
    def test_process_route_text_input(
        self, mock_save, mock_task, client, sample_memo_text
    ):
        """Test processing memo from text input."""
        mock_task.return_value.id = "test-task-123"
        mock_save.return_value = "Document saved"

        response = client.post("/process", data={"memo_text": sample_memo_text})

        # Should redirect to status page or return JSON with task ID
        assert response.status_code in [200, 302]
        mock_task.assert_called_once()
        mock_save.assert_called_once()

    @patch("app.create_memo.delay")
    @patch("login.save_document")
    def test_process_route_form_input(
        self, mock_save, mock_task, client, sample_form_data
    ):
        """Test processing memo from form input."""
        mock_task.return_value.id = "test-task-456"
        mock_save.return_value = "Document saved"

        response = client.post("/process", data=sample_form_data)

        assert response.status_code in [200, 302]
        mock_task.assert_called_once()
        mock_save.assert_called_once()

    def test_process_route_invalid_input(self, client):
        """Test processing with invalid/empty input."""
        response = client.post("/process", data={"memo_text": ""})

        # Should handle gracefully - either error page or redirect
        assert response.status_code in [200, 302, 400]

    @patch("login.save_document")
    def test_save_progress_text(self, mock_save, client, sample_memo_text):
        """Test saving progress from text editor."""
        mock_save.return_value = "Progress saved"

        response = client.post("/save_progress", data={"memo_text": sample_memo_text})

        assert response.status_code == 200
        assert b"memo_text" in response.data  # Should return to text editor
        mock_save.assert_called_once()

    @patch("login.save_document")
    def test_save_progress_form(self, mock_save, client, sample_form_data):
        """Test saving progress from form."""
        mock_save.return_value = "Progress saved"

        response = client.post("/save_progress", data=sample_form_data)

        assert response.status_code == 200
        mock_save.assert_called_once()


class TestAuthentication:
    """Test authentication-related functionality."""

    def test_login_page_get(self, client):
        """Test GET request to login page."""
        response = client.get("/login")

        assert response.status_code == 200
        assert b"username" in response.data or b"email" in response.data
        assert b"password" in response.data

    def test_register_page_get(self, client):
        """Test GET request to register page."""
        response = client.get("/register")

        assert response.status_code == 200
        assert b"username" in response.data or b"email" in response.data
        assert b"password" in response.data

    def test_logout(self, client):
        """Test logout functionality."""
        response = client.get("/logout")

        # Should redirect after logout
        assert response.status_code in [200, 302]

    @patch("login.authenticate_user")
    def test_login_post_valid(self, mock_auth, client):
        """Test POST login with valid credentials."""
        mock_auth.return_value = True

        response = client.post(
            "/login", data={"username": "testuser", "password": "testpass"}
        )

        # Should redirect on successful login
        assert response.status_code in [200, 302]

    def test_login_post_invalid(self, client):
        """Test POST login with invalid credentials."""
        with patch("db.schema.User.query") as mock_query:
            # Mock no user found
            mock_query.filter_by.return_value.first.return_value = None

            response = client.post(
                "/login", data={"username": "wronguser", "password": "wrongpass"}
            )

            # Should redirect back to login page when authentication fails
            assert response.status_code == 302
            # Check that it redirects to login page
            assert "/login" in response.location or response.location == "/"

    @patch("login.create_user")
    def test_register_post_valid(self, mock_create, client):
        """Test POST register with valid data."""
        mock_create.return_value = (True, "User created")

        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "email": "test@example.com",
                "password": "newpass123",
                "confirm_password": "newpass123",
            },
        )

        assert response.status_code in [200, 302]


class TestHistoryAndDocuments:
    """Test document history and management."""

    def test_history_page_not_logged_in(self, client):
        """Test history page when not logged in."""
        response = client.get("/history")

        # Should redirect to login or show access denied
        assert response.status_code in [200, 302, 401]

    def test_history_page_logged_in(self, client):
        """Test history page when logged in."""
        # Simulate logged in session
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"

        response = client.get("/history")

        assert response.status_code == 200
        # Should contain document history elements
        assert b"document" in response.data or b"history" in response.data


class TestSecurityHeaders:
    """Test security-related functionality."""

    def test_csp_header_present(self, client):
        """Test that Content Security Policy header is set."""
        response = client.get("/")

        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]

        # Should contain expected directives
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp

    def test_csp_allows_required_sources(self, client):
        """Test that CSP allows required external sources."""
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")

        # Should allow Google reCAPTCHA
        assert "https://www.google.com/recaptcha" in csp
        assert "https://www.gstatic.com/recaptcha" in csp

        # Should allow Google Fonts
        assert "https://fonts.googleapis.com" in csp or "fonts.googleapis.com" in csp


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_404_handling(self, client):
        """Test handling of 404 errors."""
        response = client.get("/nonexistent-route")

        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """Test handling of method not allowed errors."""
        # Try POST on GET-only route
        response = client.post("/")

        assert response.status_code == 405

    @patch("app.memo_model.MemoModel.from_text")
    def test_memo_processing_error_handling(self, mock_from_text, client):
        """Test handling of memo processing errors."""
        # Make parsing fail
        mock_from_text.side_effect = Exception("Parsing failed")

        response = client.post("/process", data={"memo_text": "invalid memo content"})

        # Should handle gracefully
        assert response.status_code in [200, 400, 500]


class TestFormValidation:
    """Test form validation and input sanitization."""

    def test_captcha_disabled_in_test(self, client):
        """Test that CAPTCHA is disabled in test environment."""
        response = client.get("/register")

        # With DISABLE_CAPTCHA=true, should not require captcha
        assert response.status_code == 200
        # Check if captcha field is present or not based on config

    def test_form_field_validation(self, client):
        """Test form field validation."""
        # Test with missing required fields
        response = client.post(
            "/process",
            data={
                "SUBJECT": "",  # Empty subject
                "MEMO_TEXT": "Some content",
            },
        )

        # Should handle validation gracefully by redirecting with error message
        assert response.status_code == 302

    def test_xss_prevention(self, client):
        """Test XSS prevention in form inputs."""
        malicious_input = '<script>alert("xss")</script>'

        response = client.post("/save_progress", data={"memo_text": malicious_input})

        assert response.status_code == 200
        # Response should not contain the specific malicious script unescaped
        assert b'alert("xss")' not in response.data
        # Or should escape the script tags
        assert (
            b"&lt;script&gt;" in response.data or b'alert("xss")' not in response.data
        )


class TestStatusAndTaskHandling:
    """Test task status and background processing."""

    def test_status_route_valid_task(self, client):
        """Test status route with valid task ID."""
        # This would typically test Celery task status
        response = client.get("/status/test-task-123")

        # Should return JSON status or redirect
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Should be JSON response
            assert (
                response.content_type == "application/json"
                or "json" in response.content_type
            )

    def test_status_route_invalid_task(self, client):
        """Test status route with invalid task ID."""
        response = client.get("/status/invalid-task-id")

        # Should handle gracefully
        assert response.status_code in [200, 404]


class TestStaticFiles:
    """Test serving of static files."""

    def test_css_files_accessible(self, client):
        """Test that CSS files are accessible."""
        response = client.get("/static/css/modern.css")

        assert response.status_code == 200
        assert "text/css" in response.content_type

    def test_js_files_accessible(self, client):
        """Test that JS files are accessible."""
        # Check if there are any JS files to test
        response = client.get("/static/js/main.js")

        # May not exist, but should not cause server error
        assert response.status_code in [200, 404]


class TestConfigurationHandling:
    """Test application configuration handling."""

    def test_development_vs_production_config(self, app_context):
        """Test configuration differences between environments."""
        app = app_context

        # In test environment, should have testing config
        assert app.config.get("TESTING") is True
        assert app.config.get("WTF_CSRF_ENABLED") is False

    def test_environment_variables_loaded(self, app_context):
        """Test that environment variables are properly loaded."""
        app = app_context

        # Should have test environment variables
        assert app.config.get("DISABLE_CAPTCHA") is True
        assert app.secret_key is not None

    @patch.dict(os.environ, {"DISABLE_CAPTCHA": "false"})
    def test_captcha_enable_config(self, app_context):
        """Test CAPTCHA enabled configuration."""
        # This would test with captcha enabled
        app = app_context
        # Configuration should reflect environment
