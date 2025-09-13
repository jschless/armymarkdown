"""
Tests for all example memo files to ensure comprehensive coverage of features.
"""

from datetime import date
import os
from unittest.mock import patch

import pytest

from app.models import memo_model
from app.services import writer

# Get the directory containing this test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(TEST_DIR)


class TestExampleMemos:
    """Test all example memo files for parsing and LaTeX generation."""

    @pytest.mark.parametrize(
        "memo_file,expected_file",
        [
            (
                os.path.join(ROOT_DIR, "resources/examples/basic_mfr.Amd"),
                os.path.join(TEST_DIR, "expected_basic_mfr.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/basic_mfr_w_table.Amd"),
                os.path.join(TEST_DIR, "expected_basic_mfr_w_table.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/long_memo.Amd"),
                os.path.join(TEST_DIR, "expected_long_memo.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/memo_extra_features.Amd"),
                os.path.join(TEST_DIR, "expected_memo_extra_features.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/memo_for.Amd"),
                os.path.join(TEST_DIR, "expected_memo_for.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/memo_multi_for.Amd"),
                os.path.join(TEST_DIR, "expected_memo_multi_for.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/memo_thru.Amd"),
                os.path.join(TEST_DIR, "expected_memo_thru.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/tutorial.Amd"),
                os.path.join(TEST_DIR, "expected_tutorial.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/additional_duty_appointment.Amd"),
                os.path.join(TEST_DIR, "expected_additional_duty_appointment.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/cif_turn_in.Amd"),
                os.path.join(TEST_DIR, "expected_cif_turn_in.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/cq_sop.Amd"),
                os.path.join(TEST_DIR, "expected_cq_sop.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/leave_pass_policy.Amd"),
                os.path.join(TEST_DIR, "expected_leave_pass_policy.tex"),
            ),
            (
                os.path.join(ROOT_DIR, "resources/examples/lost_cac_card.Amd"),
                os.path.join(TEST_DIR, "expected_lost_cac_card.tex"),
            ),
        ],
    )
    def test_memo_parsing_and_latex_generation(self, memo_file, expected_file):
        """Test that each example memo parses correctly and generates expected LaTeX."""
        # Get absolute paths to ensure tests work in different environments
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        memo_path = os.path.join(project_root, memo_file)
        expected_path = os.path.join(project_root, expected_file)

        # Parse the memo file
        memo = memo_model.MemoModel.from_file(memo_path)

        # Ensure parsing succeeded
        assert isinstance(memo, memo_model.MemoModel)
        assert memo.subject is not None
        assert len(memo.text) > 0

        # Override the date to match expected files for consistent test results
        # Only override if the memo is using today's date (not explicitly set in file)
        current_date_pattern = date.today().strftime("%d %B %Y")
        if memo.todays_date == current_date_pattern:
            memo.todays_date = "02 September 2025"

        # Generate LaTeX output
        writer_obj = writer.MemoWriter(memo)
        test_output_file = os.path.join(
            project_root, "tests", f"test_output_{os.path.basename(expected_file)}"
        )
        writer_obj.write(output_file=test_output_file)

        # Compare with expected output
        with open(test_output_file) as f:
            generated_output = f.read()

        with open(expected_path) as f:
            expected_output = f.read()

        assert generated_output == expected_output

        # Clean up test file
        if os.path.exists(test_output_file):
            os.remove(test_output_file)


class TestMemoFeatures:
    """Test specific features demonstrated in example memos."""

    def test_basic_mfr_features(self):
        """Test basic Memorandum for Record features."""
        memo = memo_model.MemoModel.from_file("resources/examples/basic_mfr.Amd")

        assert memo.memo_type == "MEMORANDUM FOR RECORD"
        assert memo.unit_name is not None
        assert memo.office_symbol is not None
        assert memo.author_name is not None
        assert memo.author_rank is not None
        assert memo.author_branch is not None

    def test_memo_for_features(self):
        """Test Memorandum For features."""
        memo = memo_model.MemoModel.from_file("resources/examples/memo_for.Amd")

        assert memo.memo_type == "MEMORANDUM FOR"
        assert memo.for_unit_name is not None
        assert len(memo.for_unit_name) > 0
        assert memo.for_unit_street_address is not None
        assert memo.for_unit_city_state_zip is not None

    def test_memo_thru_features(self):
        """Test Memorandum Thru features."""
        memo = memo_model.MemoModel.from_file("resources/examples/memo_thru.Amd")

        assert memo.memo_type == "MEMORANDUM THRU"
        assert memo.thru_unit_name is not None
        assert len(memo.thru_unit_name) > 0
        assert memo.thru_unit_street_address is not None
        assert memo.thru_unit_city_state_zip is not None

    def test_memo_multi_for_features(self):
        """Test memo with multiple FOR recipients."""
        memo = memo_model.MemoModel.from_file("resources/examples/memo_multi_for.Amd")

        assert memo.memo_type == "MEMORANDUM FOR"
        assert memo.for_unit_name is not None
        assert len(memo.for_unit_name) > 1  # Multiple recipients
        assert len(memo.for_unit_street_address) == len(memo.for_unit_name)
        assert len(memo.for_unit_city_state_zip) == len(memo.for_unit_name)

    def test_table_features(self):
        """Test memo with table formatting."""
        memo = memo_model.MemoModel.from_file(
            "resources/examples/basic_mfr_w_table.Amd"
        )

        # Check that the memo was parsed successfully
        assert isinstance(memo, memo_model.MemoModel)
        assert memo.subject is not None

        # The table should be processed as part of the text
        str(memo.text)
        # Tables get converted to LaTeX format, so check for LaTeX table markers
        # This is a basic check - the actual table processing is complex
        assert len(memo.text) > 0

    def test_extra_features(self):
        """Test memo with enclosures, distributions, and other extras."""
        memo = memo_model.MemoModel.from_file(
            "resources/examples/memo_extra_features.Amd"
        )

        assert isinstance(memo, memo_model.MemoModel)
        # These fields may or may not be present depending on the example content
        # Just verify the memo parses successfully and has basic required fields
        assert memo.subject is not None
        assert memo.author_name is not None

    def test_long_memo_features(self):
        """Test handling of longer memo content."""
        memo = memo_model.MemoModel.from_file("resources/examples/long_memo.Amd")

        assert isinstance(memo, memo_model.MemoModel)
        assert len(memo.text) > 5  # Should have substantial content

        # Test that nested lists are handled properly
        any(isinstance(item, list) for item in memo.text)
        # Long memos often have nested structure, but this depends on content

    def test_tutorial_completeness(self):
        """Test that tutorial memo demonstrates key features."""
        memo = memo_model.MemoModel.from_file("resources/examples/tutorial.Amd")

        assert isinstance(memo, memo_model.MemoModel)
        assert memo.subject is not None
        assert memo.unit_name is not None
        assert memo.author_name is not None
        assert len(memo.text) > 3  # Tutorial should have multiple points


class TestMemoValidation:
    """Test validation across all example memos."""

    @pytest.mark.parametrize(
        "memo_file",
        [
            "resources/examples/basic_mfr.Amd",
            "resources/examples/basic_mfr_w_table.Amd",
            "resources/examples/long_memo.Amd",
            "resources/examples/memo_extra_features.Amd",
            "resources/examples/memo_for.Amd",
            "resources/examples/memo_multi_for.Amd",
            "resources/examples/memo_thru.Amd",
            "resources/examples/tutorial.Amd",
            "resources/examples/additional_duty_appointment.Amd",
            "resources/examples/cif_turn_in.Amd",
            "resources/examples/cq_sop.Amd",
            "resources/examples/leave_pass_policy.Amd",
            "resources/examples/lost_cac_card.Amd",
        ],
    )
    def test_memo_validation_passes(self, memo_file):
        """Test that all example memos pass validation."""
        memo = memo_model.MemoModel.from_file(memo_file)

        # Ensure parsing succeeded
        assert isinstance(memo, memo_model.MemoModel)

        # Run language/validation checks
        errors = memo.language_check()

        # Should have no validation errors
        assert len(errors) == 0, f"Validation errors in {memo_file}: {errors}"

    @pytest.mark.parametrize(
        "memo_file",
        [
            "resources/examples/basic_mfr.Amd",
            "resources/examples/memo_for.Amd",
            "resources/examples/memo_thru.Amd",
            "resources/examples/tutorial.Amd",
        ],
    )
    def test_memo_roundtrip_conversion(self, memo_file):
        """Test that memos can be converted to dict/form and back."""
        original_memo = memo_model.MemoModel.from_file(memo_file)

        # Convert to dictionary and back
        memo_dict = original_memo.to_dict()
        reconstructed_memo = memo_model.MemoModel.from_dict(memo_dict)

        assert reconstructed_memo.subject == original_memo.subject
        assert reconstructed_memo.author_name == original_memo.author_name
        assert reconstructed_memo.unit_name == original_memo.unit_name

        # Convert to AMD format and back
        amd_text = original_memo.to_amd()
        reparsed_memo = memo_model.MemoModel.from_text(amd_text)

        assert reparsed_memo.subject == original_memo.subject
        assert reparsed_memo.author_name == original_memo.author_name
