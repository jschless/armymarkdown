"""Huey task queue configuration and memo/PDF background tasks."""

import hashlib
import logging
import os
from pathlib import Path
import random
import re
import tempfile
import time

from armymemo import parse_text, render_typst_pdf
import boto3
from botocore.exceptions import ClientError
from huey import SqliteHuey

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Huey with SQLite backend
# The database will be stored in /data for persistence across container restarts
huey = SqliteHuey(
    filename=os.environ.get("HUEY_DB_PATH", "/data/huey.db"),
    immediate=os.environ.get("HUEY_IMMEDIATE", "false").lower() == "true",
)

# S3 client initialization (lazy loaded)
_s3_client = None


def get_s3_client():
    """Get or create S3 client with lazy initialization."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            config=boto3.session.Config(
                region_name="us-east-2", signature_version="s3v4"
            ),
        )
    return _s3_client


def upload_file_to_s3(file_path, aws_path):
    """
    Upload a file to S3.

    Args:
        file_path: Local path to the file
        aws_path: Destination path in S3 bucket

    Returns:
        The file path on success, or exception on failure
    """
    s3 = get_s3_client()
    try:
        s3.upload_file(
            file_path,
            "armymarkdown",
            aws_path,
            ExtraArgs={
                "ContentType": "application/pdf",
                "ContentDisposition": "inline",
            },
        )
    except Exception as e:
        logger.error(f"S3 upload error: {e}")
        raise

    return file_path


@huey.task(retries=2, retry_delay=5)
def create_memo(text):
    """
    Create a PDF memo from AMD text.

    This task:
    1. Checks for cached PDF in S3
    2. Parses the memo with armymemo
    3. Compiles a Typst PDF
    4. Uploads to S3
    5. Returns the filename

    Args:
        text: The AMD format text content

    Returns:
        The uploaded PDF filename
    """
    start_time = time.time()
    s3 = get_s3_client()
    document = parse_text(text)
    normalized_text = document.to_amd()

    # Generate content hash for caching
    content_hash = hashlib.md5(  # nosec B324
        normalized_text.encode("utf-8")
    ).hexdigest()[:12]

    # Check for cached result in S3
    cached_filename = f"cached_{content_hash}.pdf"
    try:
        s3.head_object(Bucket="armymarkdown", Key=cached_filename)
        logger.info(f"Found cached PDF for hash {content_hash}")
        return cached_filename
    except ClientError:
        # File doesn't exist in cache, proceed with generation
        pass

    logger.debug("Generating memo subject=%s", document.subject)

    temp_name = (
        _safe_filename(document.subject)[:15]
        + "".join(random.choices("0123456789", k=4))  # nosec B311
        + ".pdf"
    )

    with tempfile.TemporaryDirectory(prefix="armymarkdown-memo-") as temp_dir_name:
        pdf_file = Path(temp_dir_name) / temp_name
        render_typst_pdf(document, pdf_file)

        try:
            s3.upload_file(
                str(pdf_file),
                "armymarkdown",
                cached_filename,
                ExtraArgs={
                    "ContentType": "application/pdf",
                    "ContentDisposition": "inline",
                },
            )
            logger.info("Cached PDF with hash %s", content_hash)
        except Exception as e:
            logger.warning(f"Failed to cache PDF: {e}")

        upload_file_to_s3(str(pdf_file), temp_name)

    generation_time = time.time() - start_time
    logger.info(f"PDF generation completed in {generation_time:.2f} seconds")

    return temp_name


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


@huey.task()
def cleanup_old_files():
    """
    Periodic task placeholder for compatibility with existing scheduler wiring.
    """
    cleaned = 0
    logger.info(f"Cleaned up {cleaned} old temporary files")
    return cleaned


def _safe_filename(subject: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]+", "_", subject.lower()).strip("_")
    return sanitized or "memo"
