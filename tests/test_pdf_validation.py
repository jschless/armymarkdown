"""
Tests for PDF validation feature.

Tests the PDF parsing service, PDF validator, and validation endpoints.
"""

import pytest


class TestPDFParser:
    """Tests for the PDFParser class."""

    def test_parser_import(self):
        """Test that PDFParser can be imported."""
        from app.services.validation import PDFMetadata, PDFParser

        assert PDFParser is not None
        assert PDFMetadata is not None

    def test_pdf_metadata_defaults(self):
        """Test PDFMetadata has correct default values."""
        from app.services.validation import PDFMetadata

        metadata = PDFMetadata()
        assert metadata.text_content == ""
        assert metadata.fonts == []
        assert metadata.margins == {}
        assert metadata.page_count == 0
        assert metadata.extraction_errors == []

    def test_parser_handles_invalid_bytes(self):
        """Test parser gracefully handles invalid PDF bytes."""
        from app.services.validation import PDFParser

        parser = PDFParser()
        metadata = parser.parse(b"not a valid pdf")

        # Should not crash, should have extraction errors
        assert len(metadata.extraction_errors) > 0

    def test_parser_handles_empty_bytes(self):
        """Test parser gracefully handles empty bytes."""
        from app.services.validation import PDFParser

        parser = PDFParser()
        metadata = parser.parse(b"")

        assert len(metadata.extraction_errors) > 0

    def test_is_likely_image_pdf_no_text(self):
        """Test detection of likely scanned/image PDFs."""
        from app.services.validation import PDFMetadata, PDFParser

        parser = PDFParser()

        # Simulate a PDF with pages but no text
        metadata = PDFMetadata()
        metadata.page_count = 2
        metadata.text_content = ""

        assert parser.is_likely_image_pdf(metadata) is True

    def test_is_likely_image_pdf_with_text(self):
        """Test detection correctly identifies text-based PDFs."""
        from app.services.validation import PDFMetadata, PDFParser

        parser = PDFParser()

        # Simulate a PDF with pages and adequate text
        metadata = PDFMetadata()
        metadata.page_count = 1
        metadata.text_content = "A" * 500  # 500 characters

        assert parser.is_likely_image_pdf(metadata) is False


class TestPDFValidator:
    """Tests for the PDFValidator class."""

    def test_validator_import(self):
        """Test that PDFValidator can be imported."""
        from app.services.validation import PDFValidationResult, PDFValidator

        assert PDFValidator is not None
        assert PDFValidationResult is not None

    def test_validation_result_to_dict(self):
        """Test PDFValidationResult serialization."""
        from app.services.validation.pdf_validator import (
            PDFValidationResult,
            ValidationIssue,
        )

        issue = ValidationIssue(
            rule_id="FONT_001",
            rule_name="Font Type",
            description="Test description",
            severity="error",
            ar_reference="AR 25-50, para 1-17",
            details="Test details",
        )

        result = PDFValidationResult(
            is_compliant=False,
            compliance_score=0.85,
            issues=[issue],
            metadata_summary={"page_count": 1},
        )

        result_dict = result.to_dict()

        assert result_dict["is_compliant"] is False
        assert result_dict["compliance_score"] == 0.85
        assert len(result_dict["issues"]) == 1
        assert result_dict["issues"][0]["rule_id"] == "FONT_001"
        assert result_dict["metadata_summary"]["page_count"] == 1

    def test_validation_issue_to_dict(self):
        """Test ValidationIssue serialization."""
        from app.services.validation.pdf_validator import ValidationIssue

        issue = ValidationIssue(
            rule_id="MARGIN_001",
            rule_name="Page Margins",
            description="All margins must be 1 inch",
            severity="warning",
            ar_reference="AR 25-50, para 1-17",
            details="Left margin: 0.5 inches",
        )

        issue_dict = issue.to_dict()

        assert issue_dict["rule_id"] == "MARGIN_001"
        assert issue_dict["rule_name"] == "Page Margins"
        assert issue_dict["severity"] == "warning"
        assert "Left margin" in issue_dict["details"]

    def test_validator_with_empty_metadata(self):
        """Test validator handles empty metadata gracefully."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Should complete without error
        assert result is not None
        assert isinstance(result.compliance_score, float)
        assert isinstance(result.issues, list)

    def test_validator_detects_missing_department_line(self):
        """Test validator detects missing DEPARTMENT OF THE ARMY header."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = "Some random memo content without proper header"
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Find HEADER_001 issue
        header_issues = [i for i in result.issues if i.rule_id == "HEADER_001"]
        assert len(header_issues) > 0, "Should detect missing department line"

    def test_validator_accepts_department_line(self):
        """Test validator accepts proper department header."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        1st Test Battalion
        123 Test Street
        Fort Test, XX 12345
        """
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Should not have HEADER_001 issue
        header_issues = [i for i in result.issues if i.rule_id == "HEADER_001"]
        assert len(header_issues) == 0, "Should accept proper department line"

    def test_validator_detects_missing_date(self):
        """Test validator detects missing or invalid date format."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        Memo content without a proper date
        """
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        date_issues = [i for i in result.issues if i.rule_id == "DATE_001"]
        assert len(date_issues) > 0, "Should detect missing date"

    def test_validator_accepts_valid_date(self):
        """Test validator accepts properly formatted date."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        15 January 2025
        SUBJECT: Test Memo
        """
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        date_issues = [i for i in result.issues if i.rule_id == "DATE_001"]
        assert len(date_issues) == 0, "Should accept valid date format"

    def test_validator_detects_missing_subject(self):
        """Test validator detects missing subject line."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        15 January 2025
        Content without subject
        """
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        subject_issues = [i for i in result.issues if i.rule_id == "SUBJECT_001"]
        assert len(subject_issues) > 0, "Should detect missing subject"

    def test_validator_accepts_subject_line(self):
        """Test validator accepts memo with subject line."""
        from app.services.validation import PDFMetadata, PDFValidator

        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        15 January 2025
        SUBJECT: Test Memo Topic
        """
        metadata.page_count = 1

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        subject_issues = [i for i in result.issues if i.rule_id == "SUBJECT_001"]
        assert len(subject_issues) == 0, "Should accept subject line"

    def test_compliance_score_calculation(self):
        """Test compliance score is calculated correctly."""
        from app.services.validation import PDFMetadata, PDFValidator

        # A well-formed memo should have high score
        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        1st Test Battalion
        123 Test Street
        Fort Test, XX 12345

        15 January 2025

        SUBJECT: Test Memorandum

        1. This is a test memo.

        JOHN A. SMITH
        CPT, EN
        Commander
        """
        metadata.page_count = 1
        metadata.fonts = [{"name": "Arial", "size": 12, "count": 100}]
        metadata.margins = {"left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0}

        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Score should be high for compliant document
        assert result.compliance_score >= 0.7


class TestValidationRules:
    """Tests for AR 25-50 validation rules."""

    def test_rules_can_be_imported(self):
        """Test that rules module can be imported."""
        from app.services.validation.rules import (
            AR_25_50_RULES,
            VALIDATION_RULES,
            Severity,
            get_all_rules,
            get_rule_by_id,
        )

        assert AR_25_50_RULES is not None
        assert VALIDATION_RULES is not None
        assert len(VALIDATION_RULES) > 0

    def test_get_rule_by_id(self):
        """Test retrieving rules by ID."""
        from app.services.validation.rules import get_rule_by_id

        rule = get_rule_by_id("FONT_001")
        assert rule is not None
        assert rule.id == "FONT_001"
        assert rule.name == "Font Type"

    def test_get_rule_by_invalid_id(self):
        """Test retrieving non-existent rule."""
        from app.services.validation.rules import get_rule_by_id

        rule = get_rule_by_id("INVALID_999")
        assert rule is None

    def test_ar_25_50_rules_structure(self):
        """Test AR 25-50 rules have expected structure."""
        from app.services.validation.rules import AR_25_50_RULES

        assert "font" in AR_25_50_RULES
        assert "margins" in AR_25_50_RULES
        assert "header" in AR_25_50_RULES
        assert "date" in AR_25_50_RULES

        # Check font rules
        assert AR_25_50_RULES["font"]["acceptable"] == ["Arial", "Courier New"]
        assert AR_25_50_RULES["font"]["size"] == 12

        # Check margin rules
        assert AR_25_50_RULES["margins"]["top"] == 1.0
        assert AR_25_50_RULES["margins"]["tolerance"] == 0.1


class TestValidationEndpoints:
    """Tests for validation API endpoints.

    Note: These tests require the full Flask app with all routes registered.
    They may be skipped if running with a minimal test app fixture.
    """

    def _route_available(self, client, route):
        """Check if a route is available (not 404)."""
        response = client.get(route)
        return response.status_code != 404

    def test_validate_page_requires_auth(self, client, auth_user):
        """Test /validate page requires authentication."""
        if not self._route_available(client, "/validate/rules"):
            pytest.skip("Validation routes not available in test app")
        auth_user.logout()
        response = client.get("/validate")
        assert response.status_code == 302  # Redirect to login

    def test_validate_page_accessible_when_authenticated(self, client, auth_user):
        """Test /validate page is accessible when authenticated."""
        if not self._route_available(client, "/validate/rules"):
            pytest.skip("Validation routes not available in test app")
        auth_user.login()
        response = client.get("/validate")
        assert response.status_code == 200

    def test_validate_pdf_requires_auth(self, client, auth_user):
        """Test /validate/pdf endpoint requires authentication."""
        if not self._route_available(client, "/validate/rules"):
            pytest.skip("Validation routes not available in test app")
        auth_user.logout()
        response = client.post("/validate/pdf")
        assert response.status_code in [302, 401]  # Redirect or unauthorized

    def test_validate_pdf_requires_file(self, client, auth_user):
        """Test /validate/pdf returns error when no file uploaded."""
        if not self._route_available(client, "/validate/rules"):
            pytest.skip("Validation routes not available in test app")
        auth_user.login()
        response = client.post("/validate/pdf")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_validate_pdf_rejects_non_pdf(self, client, auth_user):
        """Test /validate/pdf rejects non-PDF files."""
        if not self._route_available(client, "/validate/rules"):
            pytest.skip("Validation routes not available in test app")
        from io import BytesIO

        auth_user.login()
        data = {"file": (BytesIO(b"not a pdf"), "test.txt")}
        response = client.post(
            "/validate/pdf", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 400
        resp_data = response.get_json()
        assert "PDF" in resp_data.get("error", "")

    def test_validate_pdf_rejects_large_file(self, client, auth_user):
        """Test /validate/pdf rejects files over 10MB."""
        if not self._route_available(client, "/validate/rules"):
            pytest.skip("Validation routes not available in test app")
        from io import BytesIO

        auth_user.login()
        # Create a fake 11MB file
        large_content = b"x" * (11 * 1024 * 1024)
        data = {"file": (BytesIO(large_content), "large.pdf")}
        response = client.post(
            "/validate/pdf", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 400
        resp_data = response.get_json()
        assert "large" in resp_data.get("error", "").lower()

    def test_validation_rules_endpoint(self, client):
        """Test /validate/rules endpoint returns rules."""
        response = client.get("/validate/rules")
        # Skip if route not available (minimal test app)
        if response.status_code == 404:
            pytest.skip("Validation routes not available in test app")
        assert response.status_code == 200
        data = response.get_json()
        assert "rules" in data
        assert "config" in data
        assert len(data["rules"]) > 0


class TestValidationIntegration:
    """Integration tests for the full validation flow."""

    def test_validation_module_exports(self):
        """Test all expected classes are exported from validation module."""
        from app.services.validation import (
            MemoValidator,
            PDFMetadata,
            PDFParser,
            PDFValidationResult,
            PDFValidator,
            ValidationIssue,
        )

        # All should be importable
        assert MemoValidator is not None
        assert PDFParser is not None
        assert PDFMetadata is not None
        assert PDFValidator is not None
        assert PDFValidationResult is not None
        assert ValidationIssue is not None

    def test_full_validation_pipeline(self):
        """Test complete validation from parsing to results."""
        from app.services.validation import PDFMetadata, PDFValidator

        # Create metadata simulating parsed PDF
        metadata = PDFMetadata()
        metadata.text_content = """
        DEPARTMENT OF THE ARMY
        Headquarters, 1st Battalion, 1st Infantry Regiment
        123 Main Street
        Fort Test, TX 12345

        ABCD-EF                                                          15 January 2025

        MEMORANDUM FOR Record

        SUBJECT: Test of Memo Validation System

        1. This is a test memo to validate the validation system.

        2. The memo includes multiple paragraphs and proper formatting.



        JOHN A. DOE
        CPT, IN
        Commanding
        """
        metadata.page_count = 1
        metadata.fonts = [{"name": "ArialMT", "size": 12, "count": 500}]
        metadata.margins = {"left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0}

        # Run validation
        validator = PDFValidator(metadata)
        result = validator.validate_all()

        # Check result structure
        assert isinstance(result.is_compliant, bool)
        assert 0.0 <= result.compliance_score <= 1.0
        assert isinstance(result.issues, list)
        assert "page_count" in result.metadata_summary

    def test_history_page_requires_auth(self, client, auth_user):
        """Test validation history page requires authentication."""
        # Check if routes are available
        response = client.get("/validate/rules")
        if response.status_code == 404:
            pytest.skip("Validation routes not available in test app")
        auth_user.logout()
        response = client.get("/validate/history")
        assert response.status_code == 302  # Redirect to login

    def test_history_page_accessible_when_authenticated(self, client, auth_user):
        """Test validation history page is accessible when authenticated."""
        # Check if routes are available
        response = client.get("/validate/rules")
        if response.status_code == 404:
            pytest.skip("Validation routes not available in test app")
        auth_user.login()
        response = client.get("/validate/history")
        assert response.status_code == 200
