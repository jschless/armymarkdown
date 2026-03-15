"""Huey task queue configuration and PDF background tasks."""

from dataclasses import dataclass
import hashlib
import logging
import os
from pathlib import Path
import re
import tempfile
import time

from armymemo import parse_text, render_typst_pdf
from huey import SqliteHuey

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Huey with SQLite backend
# The database will be stored in /data for persistence across container restarts
huey = SqliteHuey(
    filename=os.environ.get("HUEY_DB_PATH", "/data/huey.db"),
    immediate=os.environ.get("HUEY_IMMEDIATE", "false").lower() == "true",
)


@dataclass(frozen=True, slots=True)
class RenderedMemo:
    filename: str
    pdf_bytes: bytes


def create_memo(text: str) -> RenderedMemo:
    """
    Create a PDF memo from AMD text.

    This synchronous helper:
    1. Parses the memo with armymemo
    2. Compiles a Typst PDF
    3. Returns the filename and PDF bytes directly to the caller

    Args:
        text: The AMD format text content

    Returns:
        Rendered memo filename and PDF bytes
    """
    start_time = time.time()
    document = parse_text(text)

    logger.debug("Generating memo subject=%s", document.subject)

    filename = f"{_safe_filename(document.subject)[:64]}.pdf"

    with tempfile.TemporaryDirectory(prefix="armymarkdown-memo-") as temp_dir_name:
        pdf_file = Path(temp_dir_name) / filename
        render_typst_pdf(document, pdf_file)
        pdf_bytes = pdf_file.read_bytes()

    generation_time = time.time() - start_time
    logger.info(f"PDF generation completed in {generation_time:.2f} seconds")

    return RenderedMemo(filename=filename, pdf_bytes=pdf_bytes)


@huey.task(retries=1, retry_delay=5)
def validate_pdf_task(pdf_bytes: bytes, user_id: int, filename: str):
    """
    Validate a PDF document against AR 25-50 requirements.

    This task:
    1. Parses the PDF to extract text, fonts, and margins
    2. Validates against AR 25-50 rules
    3. Stores results in the database

    Args:
        pdf_bytes: Raw PDF file content
        user_id: ID of the user who uploaded the file
        filename: Original filename of the uploaded PDF

    Returns:
        Dictionary with result_id, issues, and compliance score
    """
    from app.services.validation import PDFParser, PDFValidator
    from db.schema import ValidationResult, db

    start_time = time.time()

    # Parse the PDF
    parser = PDFParser()
    metadata = parser.parse(pdf_bytes)

    # Check if it's a scanned/image PDF
    if parser.is_likely_image_pdf(metadata):
        logger.warning(f"PDF '{filename}' appears to be scanned/image-based")

    # Validate against AR 25-50 rules
    validator = PDFValidator(metadata)
    validation_result = validator.validate_all()

    # Calculate PDF hash for caching/deduplication
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Import Flask app context for database operations
    from app.main import app

    with app.app_context():
        # Store results in database
        db_result = ValidationResult(
            user_id=user_id,
            pdf_filename=filename,
            pdf_hash=pdf_hash,
            is_compliant=validation_result.is_compliant,
            compliance_score=validation_result.compliance_score,
            issues=[issue.to_dict() for issue in validation_result.issues],
            pdf_metadata=validation_result.metadata_summary,
        )
        db.session.add(db_result)
        db.session.commit()

        result_id = db_result.id

    validation_time = time.time() - start_time
    logger.info(
        f"PDF validation completed in {validation_time:.2f}s - "
        f"Score: {validation_result.compliance_score:.0%}, "
        f"Issues: {len(validation_result.issues)}"
    )

    return {
        "result_id": result_id,
        "issues": [issue.to_dict() for issue in validation_result.issues],
        "score": validation_result.compliance_score,
        "is_compliant": validation_result.is_compliant,
    }


def _safe_filename(subject: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]+", "_", subject.lower()).strip("_")
    return sanitized or "memo"
