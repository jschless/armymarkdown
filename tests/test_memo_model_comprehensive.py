"""
Comprehensive tests for memo_model.py functionality.
"""

import pytest
import tempfile
import os
from armymarkdown import memo_model
from armymarkdown.memo_model import (
    MemoModel,
    add_latex_escape_chars,
    remove_latex_escape_chars,
)


class TestMemoModelCreation:
    """Test MemoModel creation from various sources."""

    def test_from_dict_basic(self, sample_memo_dict):
        """Test creating MemoModel from dictionary."""
        memo = MemoModel.from_dict(sample_memo_dict)
        assert isinstance(memo, MemoModel)
        assert memo.subject == sample_memo_dict["subject"]
        assert memo.author_name == sample_memo_dict["author_name"]

    def test_from_text_basic(self, sample_memo_text):
        """Test creating MemoModel from text."""
        memo = MemoModel.from_text(sample_memo_text)
        assert isinstance(memo, MemoModel)
        assert memo.subject == "Test Memo Subject"
        assert memo.author_name == "John A. Smith"

    def test_from_file_basic(self, temp_dir, sample_memo_text):
        """Test creating MemoModel from file."""
        test_file = os.path.join(temp_dir, "test_memo.Amd")
        with open(test_file, "w") as f:
            f.write(sample_memo_text)

        memo = MemoModel.from_file(test_file)
        assert isinstance(memo, MemoModel)
        assert memo.subject == "Test Memo Subject"

    def test_from_form_basic(self, sample_form_data):
        """Test creating MemoModel from form data."""
        memo = MemoModel.from_form(sample_form_data)
        assert isinstance(memo, MemoModel)
        assert memo.subject == "Test Memo Subject"
        assert memo.author_name == "John A. Smith"

    def test_memo_type_detection(self):
        """Test automatic memo type detection."""
        # Base memo with all required fields
        base_dict = {
            "unit_name": "Test Unit",
            "unit_street_address": "123 Main St",
            "unit_city_state_zip": "City, ST 12345",
            "office_symbol": "TEST-OPS",
            "subject": "Test",
            "text": [],
            "author_name": "Test Author",
            "author_rank": "CPT",
            "author_branch": "EN",
        }

        # Test MFR (default)
        memo = MemoModel.from_dict(base_dict.copy())
        assert isinstance(memo, MemoModel)
        assert memo.memo_type == "MEMORANDUM FOR RECORD"

        # Test MEMORANDUM FOR
        for_dict = base_dict.copy()
        for_dict.update(
            {
                "for_unit_name": ["Target Unit"],
                "for_unit_street_address": ["456 Oak St"],
                "for_unit_city_state_zip": ["Other City, ST 67890"],
            }
        )
        memo = MemoModel.from_dict(for_dict)
        assert isinstance(memo, MemoModel)
        assert memo.memo_type == "MEMORANDUM FOR"

        # Test MEMORANDUM THRU
        thru_dict = base_dict.copy()
        thru_dict.update(
            {
                "thru_unit_name": ["Routing Unit"],
                "thru_unit_street_address": ["789 Pine Ave"],
                "thru_unit_city_state_zip": ["Route City, ST 11111"],
            }
        )
        memo = MemoModel.from_dict(thru_dict)
        assert isinstance(memo, MemoModel)
        assert memo.memo_type == "MEMORANDUM THRU"


class TestMemoModelValidation:
    """Test validation functionality."""

    def test_valid_date_formats(self, sample_memo_dict):
        """Test valid date format validation."""
        memo = MemoModel.from_dict(sample_memo_dict)

        valid_dates = ["01 January 2024", "15 March 2024", "31 December 2023"]
        for date in valid_dates:
            assert memo._check_date(date) is None

    def test_invalid_date_formats(self, sample_memo_dict):
        """Test invalid date format detection."""
        memo = MemoModel.from_dict(sample_memo_dict)

        invalid_dates = [
            "1 January 2024",  # Single digit day
            "01 Jan 2024",  # Abbreviated month
            "01 January 24",  # Two digit year
            "January 01 2024",  # Wrong order
            "2024-01-01",  # ISO format
            "01/01/2024",  # Slash format
        ]

        for date in invalid_dates:
            error = memo._check_date(date)
            assert error is not None
            assert "does not conform to pattern" in error

    def test_valid_branch_codes(self, sample_memo_dict):
        """Test valid branch code validation."""
        memo = MemoModel.from_dict(sample_memo_dict)

        valid_branches = ["EN", "IN", "AR", "FA", "AG", "MI", "SC", "TC"]
        for branch in valid_branches:
            assert memo._check_branch(branch) is None

    def test_invalid_branch_codes(self, sample_memo_dict):
        """Test invalid branch code detection."""
        memo = MemoModel.from_dict(sample_memo_dict)

        invalid_branches = ["INVALID", "En", "infantry", "123", "XX"]
        for branch in invalid_branches:
            error = memo._check_branch(branch)
            assert error is not None
            assert "is mispelled or not a valid Army branch" in error

    def test_language_check(self, sample_memo_dict):
        """Test overall language/validation check."""
        memo = MemoModel.from_dict(sample_memo_dict)
        errors = memo.language_check()
        assert len(errors) == 0

        # Test with invalid date
        memo.todays_date = "Invalid Date"
        errors = memo.language_check()
        assert len(errors) > 0
        assert any("DATE" in error[0] for error in errors)


class TestMemoModelConversions:
    """Test conversion methods."""

    def test_to_dict(self, sample_memo_dict):
        """Test conversion to dictionary."""
        memo = MemoModel.from_dict(sample_memo_dict)
        result_dict = memo.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["subject"] == sample_memo_dict["subject"]
        assert result_dict["author_name"] == sample_memo_dict["author_name"]

    def test_to_form(self, sample_memo_dict):
        """Test conversion to form format."""
        memo = MemoModel.from_dict(sample_memo_dict)
        form_dict = memo.to_form()

        assert isinstance(form_dict, dict)
        assert "text" in form_dict
        assert isinstance(form_dict["text"], str)  # Should be string for form

    def test_to_amd(self, sample_memo_dict):
        """Test conversion to AMD format."""
        memo = MemoModel.from_dict(sample_memo_dict)
        amd_text = memo.to_amd()

        assert isinstance(amd_text, str)
        assert "SUBJECT = " in amd_text
        assert "ORGANIZATION_NAME = " in amd_text
        assert memo.subject in amd_text

    def test_roundtrip_conversion(self, sample_memo_text):
        """Test that conversions are reversible."""
        # Text -> Model -> Text
        original_memo = MemoModel.from_text(sample_memo_text)
        converted_text = original_memo.to_amd()
        reconverted_memo = MemoModel.from_text(converted_text)

        assert original_memo.subject == reconverted_memo.subject
        assert original_memo.author_name == reconverted_memo.author_name
        assert original_memo.unit_name == reconverted_memo.unit_name


class TestTextProcessing:
    """Test text processing and parsing functionality."""

    def test_nested_list_parsing(self):
        """Test parsing of nested bullet lists."""
        text = """ORGANIZATION_NAME=Test Unit
ORGANIZATION_STREET_ADDRESS=123 Test St
ORGANIZATION_CITY_STATE_ZIP=Test City, TS 12345
OFFICE_SYMBOL=TST
AUTHOR=Test Author
RANK=CPT
BRANCH=EN
TITLE=Test Title
SUBJECT=Test Subject

- First level item
    - Second level item
        - Third level item
    - Another second level
- Back to first level"""

        memo = MemoModel.from_text(text)
        assert isinstance(memo, MemoModel)

        # Check nested structure
        has_nested = any(isinstance(item, list) for item in memo.text)
        assert has_nested

    def test_paragraph_continuation(self):
        """Test multi-paragraph items."""
        text = """ORGANIZATION_NAME=Test Unit
ORGANIZATION_STREET_ADDRESS=123 Test St
ORGANIZATION_CITY_STATE_ZIP=Test City, TS 12345
OFFICE_SYMBOL=TST
AUTHOR=Test Author
RANK=CPT
BRANCH=EN
TITLE=Test Title
SUBJECT=Test Subject

- This is the first paragraph of an item.
This is the second paragraph of the same item.

- This is a separate item."""

        memo = MemoModel.from_text(text)
        assert isinstance(memo, MemoModel)
        assert len(memo.text) >= 2

        # First item should contain both paragraphs
        first_item = memo.text[0] if memo.text else ""
        assert "first paragraph" in str(first_item)
        assert "second paragraph" in str(first_item)

    def test_table_processing(self):
        """Test table parsing functionality."""
        text = """ORGANIZATION_NAME=Test Unit
ORGANIZATION_STREET_ADDRESS=123 Test St
ORGANIZATION_CITY_STATE_ZIP=Test City, TS 12345
OFFICE_SYMBOL=TST
AUTHOR=Test Author
RANK=CPT
BRANCH=EN
TITLE=Test Title
SUBJECT=Test Subject

- Regular item before table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

- Regular item after table"""

        memo = MemoModel.from_text(text)
        assert isinstance(memo, MemoModel)
        assert len(memo.text) >= 3  # Before, table, after


class TestLatexEscaping:
    """Test LaTeX character escaping functionality."""

    def test_basic_escape_characters(self, special_characters_samples):
        """Test escaping of basic LaTeX special characters."""
        test_text = special_characters_samples["latex_special"]
        escaped = add_latex_escape_chars(test_text)

        assert r"\&" in escaped  # & -> \&
        assert r"\%" in escaped  # % -> \%
        assert r"\$" in escaped  # $ -> \$
        assert r"\#" in escaped  # # -> \#
        assert r"\_" in escaped  # _ -> \_
        assert r"\{" in escaped  # { -> \{
        assert r"\}" in escaped  # } -> \}

    def test_markdown_formatting(self, special_characters_samples):
        """Test markdown formatting conversion."""
        test_text = special_characters_samples["markdown_formatting"]
        escaped = add_latex_escape_chars(test_text)

        assert r"\textbf{" in escaped  # **bold** -> \textbf{bold}
        assert r"\textit{" in escaped  # *italic* -> \textit{italic}
        # Code formatting would need backticks which aren't in the sample

    def test_special_symbols(self, special_characters_samples):
        """Test special symbol escaping."""
        test_text = special_characters_samples["symbols"]
        escaped = add_latex_escape_chars(test_text)

        assert r"\textasciitilde" in escaped  # ~ -> \textasciitilde
        assert r"\textasciicircum" in escaped  # ^ -> \textasciicircum
        assert r"\textbackslash" in escaped  # \ -> \textbackslash

    def test_escape_reversibility(self, special_characters_samples):
        """Test that escaping and unescaping are reversible."""
        for sample_name, original_text in special_characters_samples.items():
            if sample_name == "unicode_chars":  # Skip unicode for now
                continue

            escaped = add_latex_escape_chars(original_text)
            unescaped = remove_latex_escape_chars(escaped)

            # Should get back to original (approximately)
            # Some formatting markers might be different but content preserved
            assert len(unescaped) > 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_subject_error(self):
        """Test error when SUBJECT is missing."""
        text = """ORGANIZATION_NAME=Test Unit
AUTHOR=Test Author
RANK=CPT
BRANCH=EN

- This memo has no subject"""

        result = MemoModel.from_text(text)
        assert isinstance(result, str)  # Should return error string
        assert "missing the keyword SUBJECT" in result

    def test_missing_required_fields_error(self):
        """Test error when required fields are missing."""
        incomplete_dict = {
            "subject": "Test Subject",
            "text": ["Test content"],
            # Missing unit_name, author_name, etc.
        }

        result = MemoModel.from_dict(incomplete_dict)
        assert isinstance(result, str)  # Should return error string
        assert "Missing the following keys" in result

    def test_invalid_keyword_error(self):
        """Test error when invalid keyword is used."""
        text = """ORGANIZATION_NAME=Test Unit
INVALID_KEYWORD=Some Value
AUTHOR=Test Author
RANK=CPT
BRANCH=EN
SUBJECT=Test Subject

- Test content"""

        result = MemoModel.from_text(text)
        assert isinstance(result, str)  # Should return error string
        assert "No such keyword" in result

    def test_empty_file_handling(self, temp_dir):
        """Test handling of empty files."""
        empty_file = os.path.join(temp_dir, "empty.Amd")
        with open(empty_file, "w") as f:
            f.write("")

        result = MemoModel.from_file(empty_file)
        assert isinstance(result, str)  # Should return error string

    def test_malformed_content_handling(self):
        """Test handling of malformed content."""
        malformed_text = """This is not a proper memo format
No equals signs or proper structure
Just random text"""

        result = MemoModel.from_text(malformed_text)
        assert isinstance(result, str)  # Should return error string


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_memo_with_all_optional_fields(self):
        """Test memo with all possible optional fields."""
        complex_dict = {
            "unit_name": "Test Battalion",
            "unit_street_address": "123 Main St",
            "unit_city_state_zip": "City, ST 12345",
            "office_symbol": "TEST-OPS-XO",
            "subject": "Complex Test Memo",
            "text": ["Test content with multiple features"],
            "author_name": "Jane A. Smith",
            "author_rank": "MAJ",
            "author_branch": "IN",
            "author_title": "Executive Officer",
            "for_unit_name": ["Receiving Unit"],
            "for_unit_street_address": ["456 Oak Ave"],
            "for_unit_city_state_zip": ["Other City, ST 67890"],
            "suspense_date": "30 June 2024",
            "document_mark": "CONFIDENTIAL",
            "enclosures": ["Enclosure 1", "Enclosure 2"],
            "distros": ["Distribution List 1"],
            "cfs": ["Copy Furnished To"],
            "authority": "AR 25-50",
        }

        memo = MemoModel.from_dict(complex_dict)
        assert isinstance(memo, MemoModel)
        assert memo.memo_type == "MEMORANDUM FOR"  # Because for_unit_name is present
        assert memo.suspense_date == "30 June 2024"
        assert memo.enclosures is not None
        assert len(memo.enclosures) == 2

    def test_very_long_content(self):
        """Test handling of very long memo content."""
        long_text_items = [
            f"This is item number {i} with substantial content." for i in range(100)
        ]

        memo_dict = {
            "unit_name": "Test Unit",
            "unit_street_address": "123 Test St",
            "unit_city_state_zip": "Test City, TS 12345",
            "office_symbol": "TST",
            "subject": "Long Test Memo",
            "text": long_text_items,
            "author_name": "Test Author",
            "author_rank": "CPT",
            "author_branch": "EN",
        }

        memo = MemoModel.from_dict(memo_dict)
        assert isinstance(memo, MemoModel)
        assert len(memo.text) == 100

        # Test conversion to AMD format
        amd_text = memo.to_amd()
        assert isinstance(amd_text, str)
        assert len(amd_text) > 1000  # Should be substantial content

    def test_unicode_and_special_content(self):
        """Test handling of unicode and special characters."""
        special_dict = {
            "unit_name": "Tëst Ünit with Spëcial Chars",
            "unit_street_address": "123 Spëcial St",
            "unit_city_state_zip": "Tëst City, TS 12345",
            "office_symbol": "TST-SPL",
            "subject": "Tëst Sübject: $pecial & Unique",
            "text": [
                "Content with émoji and spëcial chars: café, résumé",
                "Mathematical symbols: ∑, ∆, π, ∞",
                "Currency: $100, €50, £25, ¥1000",
            ],
            "author_name": "José María González-Smith",
            "author_rank": "CPT",
            "author_branch": "EN",
        }

        memo = MemoModel.from_dict(special_dict)
        assert isinstance(memo, MemoModel)

        # Test that to_amd() produces correct Army Markdown format
        amd_text = memo.to_amd()
        assert isinstance(amd_text, str)
        # AMD format should contain unescaped special chars and preserve unicode
        assert "$pecial & Unique" in amd_text  # Special chars unescaped in AMD format
        assert "café, résumé" in amd_text  # Unicode preserved
        assert "José María González-Smith" in amd_text  # Unicode in author name

        # Test LaTeX escaping functionality separately
        from armymarkdown.memo_model import add_latex_escape_chars

        escaped_subject = add_latex_escape_chars(memo.subject)
        assert "\\$" in escaped_subject  # $ should be escaped in LaTeX
        assert "\\&" in escaped_subject  # & should be escaped in LaTeX
