"""
Huey task queue configuration and tasks.

This module provides background task processing using Huey with SQLite backend,
replacing the previous Celery + Redis setup for simpler deployment.
"""

import hashlib
import logging
import os
import random
import time

import boto3
from botocore.exceptions import ClientError
from huey import SqliteHuey

from app.models import memo_model
from app.services import writer

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
    ret_val = None
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
        ret_val = file_path
    except Exception as e:
        logger.error(f"S3 upload error: {e}")
        ret_val = e

    # Delete file after upload
    if os.path.exists(file_path):
        os.remove(file_path)
    return ret_val


@huey.task(retries=2, retry_delay=5)
def create_memo(text, dictionary=None):
    """
    Create a PDF memo from text or form dictionary.

    This task:
    1. Checks for cached PDF in S3
    2. Generates LaTeX document
    3. Compiles to PDF
    4. Uploads to S3
    5. Returns the filename

    Args:
        text: The AMD format text content
        dictionary: Optional form dictionary (takes precedence over text)

    Returns:
        The .tex filename (caller converts to .pdf for download link)
    """
    start_time = time.time()
    s3 = get_s3_client()

    # Parse input
    if dictionary and isinstance(dictionary, dict):
        m = memo_model.MemoModel.from_form(dictionary)
        content_for_hash = str(sorted(dictionary.items()))
    else:
        m = memo_model.MemoModel.from_text(text)
        content_for_hash = text

    # Generate content hash for caching
    content_hash = hashlib.md5(  # nosec B324
        content_for_hash.encode("utf-8")
    ).hexdigest()[:12]

    # Check for cached result in S3
    cached_filename = f"cached_{content_hash}.pdf"
    try:
        s3.head_object(Bucket="armymarkdown", Key=cached_filename)
        logger.info(f"Found cached PDF for hash {content_hash}")
        return cached_filename.replace(".pdf", ".tex")
    except ClientError:
        # File doesn't exist in cache, proceed with generation
        pass

    logger.debug(f"Generating memo: {m.to_dict()}")

    # Create MemoWriter and generate files
    mw = writer.MemoWriter(m)

    # Generate unique temp filename
    temp_name = (
        m.subject.replace(" ", "_").lower()[:15]
        + "".join(random.choices("0123456789", k=4))  # nosec B311
        + ".tex"
    )

    # Use /app directory for temp files in container
    app_root = os.environ.get("APP_ROOT", "/app")
    file_path = os.path.join(app_root, temp_name)

    # Write LaTeX file
    mw.write(output_file=file_path)

    # Compile PDF
    mw.generate_memo()

    # Upload generated PDF to cache
    pdf_file = file_path.replace(".tex", ".pdf")
    if os.path.exists(pdf_file):
        try:
            # Upload to cache location
            s3.upload_file(
                pdf_file,
                "armymarkdown",
                cached_filename,
                ExtraArgs={
                    "ContentType": "application/pdf",
                    "ContentDisposition": "inline",
                },
            )
            logger.info(f"Cached PDF with hash {content_hash}")
        except Exception as e:
            logger.warning(f"Failed to cache PDF: {e}")

    # Upload to regular location
    if os.path.exists(pdf_file):
        upload_file_to_s3(pdf_file, temp_name[:-4] + ".pdf")
    else:
        raise FileNotFoundError(f"PDF at path {pdf_file} was not created")

    # Clean up temp files
    file_endings = [".aux", ".fdb_latexmk", ".fls", ".log", ".out", ".tex"]
    for ending in file_endings:
        temp = file_path[:-4] + ending
        if os.path.exists(temp):
            os.remove(temp)

    generation_time = time.time() - start_time
    logger.info(f"PDF generation completed in {generation_time:.2f} seconds")

    return temp_name


@huey.task()
def cleanup_old_files():
    """
    Periodic task to clean up old temporary files.
    Run this periodically to prevent disk space issues.
    """
    app_root = os.environ.get("APP_ROOT", "/app")
    cleaned = 0
    for filename in os.listdir(app_root):
        if filename.endswith((".aux", ".log", ".out", ".fls", ".fdb_latexmk")):
            file_path = os.path.join(app_root, filename)
            # Only delete files older than 1 hour
            if os.path.getmtime(file_path) < time.time() - 3600:
                try:
                    os.remove(file_path)
                    cleaned += 1
                except OSError:
                    pass
    logger.info(f"Cleaned up {cleaned} old temporary files")
    return cleaned
