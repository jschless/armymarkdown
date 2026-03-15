from pathlib import Path
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from app.tasks import create_memo


def test_create_memo_renders_pdf_and_uploads(sample_memo_text, tmp_path):
    mock_s3 = Mock()

    def fake_render(document, output_path):
        Path(output_path).write_bytes(b"%PDF-1.7 test pdf")
        return Path(output_path)

    with (
        patch("app.tasks.get_s3_client", return_value=mock_s3),
        patch("app.tasks.render_typst_pdf", side_effect=fake_render) as mock_render,
        patch("app.tasks.upload_file_to_s3") as mock_upload,
    ):
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )

        filename = create_memo.call_local(sample_memo_text)

    assert filename.endswith(".pdf")
    mock_render.assert_called_once()
    mock_s3.upload_file.assert_called_once()
    mock_upload.assert_called_once()


def test_create_memo_returns_cached_filename(sample_memo_text):
    mock_s3 = Mock()

    with (
        patch("app.tasks.get_s3_client", return_value=mock_s3),
        patch("app.tasks.render_typst_pdf") as mock_render,
        patch("app.tasks.upload_file_to_s3") as mock_upload,
    ):
        filename = create_memo.call_local(sample_memo_text)

    assert filename.startswith("cached_")
    assert filename.endswith(".pdf")
    mock_render.assert_not_called()
    mock_upload.assert_not_called()
