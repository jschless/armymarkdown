from pathlib import Path
from unittest.mock import Mock, patch

from app.tasks import (
    RenderedMemo,
    create_memo,
    review_memo_content,
    review_memo_content_live,
)


def test_create_memo_renders_pdf_bytes(sample_memo_text):
    def fake_render(document, output_path):
        Path(output_path).write_bytes(b"%PDF-1.7 test pdf")
        return Path(output_path)

    with patch("app.tasks.render_typst_pdf", side_effect=fake_render) as mock_render:
        rendered = create_memo(sample_memo_text)

    assert isinstance(rendered, RenderedMemo)
    assert rendered.filename.endswith(".pdf")
    assert rendered.pdf_bytes == b"%PDF-1.7 test pdf"
    mock_render.assert_called_once()


def test_create_memo_uses_safe_subject_filename():
    sample_memo_text = """ORGANIZATION_NAME = Test Unit
ORGANIZATION_STREET_ADDRESS = 123 Main St
ORGANIZATION_CITY_STATE_ZIP = Test, ST 12345
OFFICE_SYMBOL = TEST
AUTHOR = Test User
RANK = CPT
BRANCH = EN
SUBJECT = Memo / With Unsafe : Characters?

- This is a test memo.
"""

    def fake_render(document, output_path):
        Path(output_path).write_bytes(b"%PDF-1.7 test pdf")
        return Path(output_path)

    with patch("app.tasks.render_typst_pdf", side_effect=fake_render) as mock_render:
        rendered = create_memo(sample_memo_text)

    assert rendered.filename == "memo_with_unsafe_characters.pdf"
    mock_render.assert_called_once()


def test_review_memo_content_returns_structured_report(sample_memo_text):
    fake_report = Mock()
    fake_report.passed = False
    fake_report.failed_rules = 2

    def fake_render(document, output_path):
        Path(output_path).write_bytes(b"%PDF-1.7 test pdf")
        return Path(output_path)

    with (
        patch(
            "app.tasks.parse_text", return_value=Mock(subject="Review Subject")
        ) as mock_parse,
        patch("app.tasks.render_typst_pdf", side_effect=fake_render) as mock_render,
        patch("app.tasks.review_document", return_value=fake_report) as mock_review,
    ):
        report = review_memo_content(sample_memo_text)

    assert report is fake_report
    mock_parse.assert_called_once_with(sample_memo_text)
    mock_render.assert_called_once()
    mock_review.assert_called_once()


def test_review_memo_content_live_uses_document_only_rules(sample_memo_text):
    fake_report = Mock()
    fake_report.passed = True
    fake_report.failed_rules = 0

    with (
        patch(
            "app.tasks.parse_text", return_value=Mock(subject="Review Subject")
        ) as mock_parse,
        patch("app.tasks.review_document", return_value=fake_report) as mock_review,
    ):
        report = review_memo_content_live(sample_memo_text)

    assert report is fake_report
    mock_parse.assert_called_once_with(sample_memo_text)
    mock_review.assert_called_once()
    assert "rules" in mock_review.call_args.kwargs
