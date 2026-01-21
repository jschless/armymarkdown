"""
Integration tests for the memo validation feature.

Tests the complete flow from PDF upload through validation to results display.
"""

import pytest


class TestValidationFlow:
    """Test the complete validation workflow."""

    def test_validation_module_initialization(self):
        """Test that validation module initializes correctly."""
        from app.services.validation import (
            MemoValidator,
            PDFParser,
            PDFValidator,
        )

        # Create instances to verify no initialization errors
        parser = PDFParser()
        assert parser is not None

        # MemoValidator needs data
        validator = MemoValidator({})
        assert validator is not None

    def test_memo_validator_validates_text(self):
        """Test MemoValidator can validate AMD format text."""
        from app.services.validation import MemoValidator

        valid_text = """ORGANIZATION_NAME=1st Test Battalion
ORGANIZATION_STREET_ADDRESS=123 Test Street
ORGANIZATION_CITY_STATE_ZIP=Fort Test, TX 12345
OFFICE_SYMBOL=ABCD-EF
DATE=15 January 2025
AUTHOR=John A. Smith
RANK=CPT
BRANCH=EN

SUBJECT=Test Memo

---
- This is a test memo.
- Point of contact is the undersigned.
"""
        result = MemoValidator.validate_text_input(valid_text)

        # Should be valid or have only warnings
        assert result is not None
        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")

    def test_memo_validator_detects_invalid_date(self):
        """Test MemoValidator detects invalid date format."""
        from app.services.validation import MemoValidator

        invalid_text = """ORGANIZATION_NAME=1st Test Battalion
ORGANIZATION_STREET_ADDRESS=123 Test Street
ORGANIZATION_CITY_STATE_ZIP=Fort Test, TX 12345
OFFICE_SYMBOL=ABCD-EF
DATE=01/15/2025
AUTHOR=John A. Smith
RANK=CPT
BRANCH=EN

SUBJECT=Test Memo

---
- This is a test memo.
"""
        result = MemoValidator.validate_text_input(invalid_text)

        # Should have date format error
        assert result is not None
        date_errors = [e for e in result.errors if "Date" in e or "date" in e.lower()]
        assert len(date_errors) > 0

    def test_pdf_validator_full_check(self):
        """Test PDFValidator runs all validation checks."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        SUBJECT: Test Memo
        15 January 2025
        CPT John Smith
        """
        metadata.page_count = 1
        metadata.fonts = [{"name": "Arial", "size": 12, "count": 100}]
        metadata.margins = {"left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0}

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Result should have all expected fields
        assert hasattr(result, "is_compliant")
        assert hasattr(result, "compliance_score")
        assert hasattr(result, "issues")
        assert hasattr(result, "metadata_summary")

        # Metadata summary should have page info
        assert "page_count" in result.metadata_summary
        assert result.metadata_summary["page_count"] == 1

    def test_validation_result_serialization(self):
        """Test validation results can be serialized to JSON."""
        import json

        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = "Test content"
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Convert to dict and then to JSON
        result_dict = result.to_dict()
        json_str = json.dumps(result_dict)

        # Should be valid JSON
        assert json_str is not None
        parsed = json.loads(json_str)
        assert "is_compliant" in parsed
        assert "compliance_score" in parsed
        assert "issues" in parsed


class TestValidationEndpointFlow:
    """Test validation endpoints work together.

    Note: These tests require the full Flask app with all routes registered.
    They may be skipped if running with a minimal test app fixture.
    """

    def test_rules_endpoint_structure(self, client):
        """Test validation rules endpoint returns proper structure."""
        response = client.get("/validate/rules")
        # Skip if route not available (minimal test app)
        if response.status_code == 404:
            pytest.skip("Validation routes not available in test app")

        assert response.status_code == 200

        data = response.get_json()

        # Check structure
        assert "rules" in data
        assert "config" in data

        # Check rules have expected fields
        for rule in data["rules"]:
            assert "id" in rule
            assert "name" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "ar_reference" in rule

        # Check config has expected sections
        assert "font" in data["config"]
        assert "margins" in data["config"]

    def test_protected_routes_redirect_unauthenticated(self, client, auth_user):
        """Test protected validation routes redirect unauthenticated users."""
        # Check if routes are available
        response = client.get("/validate/rules")
        if response.status_code == 404:
            pytest.skip("Validation routes not available in test app")

        auth_user.logout()

        # All these should redirect to login
        protected_routes = [
            "/validate",
            "/validate/history",
        ]

        for route in protected_routes:
            response = client.get(route)
            # Should redirect (302) or return unauthorized (401)
            assert response.status_code in [302, 401], (
                f"Route {route} should be protected"
            )


class TestValidationScoreCalculation:
    """Test validation score calculation logic."""

    def test_perfect_score_no_issues(self):
        """Test document with no issues gets high score."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        1st Test Battalion
        123 Test Street
        Fort Test, TX 12345

        ABCD-EF                                                  15 January 2025

        SUBJECT: Test Memo

        1. This is a test paragraph.

        JOHN A. SMITH
        CPT, EN
        Commanding
        """
        metadata.page_count = 1
        metadata.fonts = [{"name": "Arial", "size": 12, "count": 200}]
        metadata.margins = {"left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0}

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Score should be reasonably high
        assert result.compliance_score >= 0.5

    def test_low_score_many_issues(self):
        """Test document with many issues gets lower score."""
        from app.services.validation import PDFMetadata, PDFValidator

        # Minimal document missing many required elements
        metadata = PDFMetadata()
        metadata.text_content = "Just some random text with no proper formatting"
        metadata.page_count = 1
        metadata.fonts = []  # No fonts detected
        metadata.margins = {}  # No margins detected

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Should have issues
        assert len(result.issues) > 0

        # Score should reflect issues
        assert result.compliance_score < 1.0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_text_content(self):
        """Test handling of empty text content."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = ""
        metadata.page_count = 0

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Should complete without error
        assert result is not None

    def test_unicode_content(self):
        """Test handling of unicode characters in content."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        SUBJECT: Test with unicode — "quotes" and résumé
        15 January 2025
        """
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Should complete without error
        assert result is not None

    def test_very_long_content(self):
        """Test handling of very long document content."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        # Create a long document
        metadata.text_content = (
            """
        DEPARTMENT OF THE ARMY
        SUBJECT: Very Long Memo
        15 January 2025
        """
            + "\n1. Test paragraph. " * 1000
        )
        metadata.page_count = 10

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Should complete without error
        assert result is not None
        assert result.metadata_summary["page_count"] == 10

    def test_special_characters_in_content(self):
        """Test handling of special characters."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        SUBJECT: Test with & % $ # @ special chars
        15 January 2025
        """
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Should complete without error
        assert result is not None
