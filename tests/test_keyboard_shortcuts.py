"""Tests for keyboard shortcuts functionality"""

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


class TestKeyboardShortcuts:
    """Test keyboard shortcuts integration"""

    def test_keyboard_shortcuts_js_included_in_index(self, client):
        """Test that keyboard shortcuts JS is included in index page"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"keyboard-shortcuts.js" in response.data

    def test_keyboard_shortcuts_js_included_in_form(self, client):
        """Test that keyboard shortcuts JS is included in form page"""
        response = client.get("/form")
        assert response.status_code == 200
        assert b"keyboard-shortcuts.js" in response.data

    def test_shortcuts_help_button_in_navigation(self, client):
        """Test that shortcuts help button is in navigation"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"showShortcutsHelp" in response.data
        # Check for keyboard emoji in UTF-8 encoded form
        assert "⌨️".encode() in response.data

    def test_keyboard_shortcuts_css_styles_present(self, client):
        """Test that keyboard shortcuts CSS is loaded"""
        response = client.get("/static/css/custom.css")
        assert response.status_code == 200
        assert b"shortcuts-help-overlay" in response.data
        assert b"shortcut-feedback" in response.data

    def test_keyboard_shortcuts_file_exists(self, client):
        """Test that keyboard shortcuts JS file is accessible"""
        response = client.get("/static/keyboard-shortcuts.js")
        assert response.status_code == 200
        assert b"KeyboardShortcuts" in response.data
        assert b"handleSave" in response.data
        assert b"handleGenerate" in response.data
        assert b"handleOpen" in response.data
