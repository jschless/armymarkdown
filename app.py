import random
import os
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    jsonify,
    flash,
)
from celery import Celery
import logging
import boto3
from botocore.exceptions import ClientError
from armymarkdown import memo_model, writer
from flask_talisman import Talisman
from db.db import init_db
from login import save_document

if "REDIS_URL" not in os.environ:
    # set os.environ from local_config
    from local_config import config

    for key, val in config.items():
        os.environ[key] = val

app = Flask(__name__, static_url_path="/static")
app.secret_key = os.environ["FLASK_SECRET"]
app.config["RECAPTCHA_PUBLIC_KEY"] = os.environ["RECAPTCHA_PUBLIC_KEY"]
app.config["RECAPTCHA_PRIVATE_KEY"] = os.environ["RECAPTCHA_PRIVATE_KEY"]

celery = Celery(
    app.name,
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
    broker_connection_retry_on_startup=True,
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/users.db"


if os.environ.get("DEVELOPMENT") is not None:
    app.debug = True
    app.logger.setLevel(logging.DEBUG)

init_db(app)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    config=boto3.session.Config(region_name="us-east-2", signature_version="s3v4"),
)


@app.after_request
def add_csp(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://www.google.com/recaptcha/api.js "
        "https://www.gstatic.com/recaptcha/; "  # Allow scripts from trusted sources
        "font-src 'self' https://fonts.gstatic.com https://fonts.google.com "
        "https://www.gstatic.com data:; "  # Allow data URIs for fonts
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "  # Allow inline styles if necessary
        "frame-src https://www.google.com;"
        "img-src 'self'; "  # Only allow images from the same origin
        "connect-src 'self';"  # Only allow AJAX/fetch calls to the same origin
    )
    return response


@app.route("/", methods=["GET"])
def index():
    example_file = process_example_file(request.args)

    return render_template(
        "index.html",
        memo_text=open(os.path.join("./examples", example_file), "r").read(),
    )


def process_example_file(args):
    example_file = args.get("example_file", "tutorial.Amd")

    if example_file not in os.listdir("./examples"):
        example_file = "./tutorial.Amd"

    return example_file


@app.route("/form", methods=["GET"])
def form():
    example_file = process_example_file(request.args)

    m = memo_model.MemoModel.from_file(os.path.join("./examples", example_file))
    memo_dict = m.to_form()

    return render_template("memo_form.html", **memo_dict)


@app.route("/save_progress", methods=["POST"])
def save_progress():
    if "SUBJECT" not in request.form:
        text = request.form.get("memo_text")
        res = save_document(text)
        flash(res)
        return render_template("index.html", memo_text=text)

    else:
        m = memo_model.MemoModel.from_form(request.form.to_dict())
        text = m.to_amd()
        res = save_document(text)
        flash(res)
        return render_template("memo_form.html", **m.to_form())


def check_memo(text):
    m = memo_model.MemoModel.from_text(text)

    if isinstance(m, str):
        # rudimentary error handling
        return m.strip()

    errors = m.language_check()
    if len(errors) > 0:
        return "\n".join([f"Error with {k}: {v}" for k, v in errors])

    return None


@app.route("/process", methods=["POST"])
def process():
    if "SUBJECT" not in request.form:
        # came from the text page
        text = request.form.get("memo_text")
        task = create_memo.delay(text)
    else:
        m = memo_model.MemoModel.from_form(request.form.to_dict())
        text = m.to_amd()
        task = create_memo.delay("", request.form.to_dict())

    res = save_document(text)
    flash(res)

    # memo_errors = check_memo(text)
    # if memo_errors is not None:
    #     return memo_errors, 400
    return (
        "Hi, we're waiting for your PDF to be created.",
        200,
        {"Location": url_for("taskstatus", task_id=task.id)},
    )


def process_task(task, result_func):
    if task.state == "PENDING":
        # job did not start yet
        response = {"state": task.state, "status": "Pending..."}
    elif task.state == "SUCCESS":
        result = task.result
        response = {
            "state": task.state,
            "result": result_func(result),
            "presigned_url": get_aws_link(result_func(result)),
        }
        task.forget()
    else:
        # something went wrong in the background job
        response = {
            "state": task.state,
            "status": str(task.info),  # this is the exception raised
        }
    return response


@app.route("/status/<task_id>", methods=["POST", "GET"])
def taskstatus(task_id):
    task = create_memo.AsyncResult(task_id)
    return jsonify(process_task(task, lambda res: res[:-4] + ".pdf"))


def get_aws_link(file_name):
    """
    Generate presigned URL for S3 object with proper error handling.

    Args:
        file_name (str): S3 object key

    Returns:
        str: Presigned URL or None on error
    """
    from constants import S3_BUCKET_NAME, PRESIGNED_URL_EXPIRY_SECONDS

    if not file_name:
        app.logger.error("get_aws_link called with empty file_name")
        return None

    try:
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": file_name},
            ExpiresIn=PRESIGNED_URL_EXPIRY_SECONDS,
        )
        app.logger.debug(f"Generated presigned URL for {file_name}")
        return response

    except ClientError as e:
        error_code = e.response['Error']['Code']
        app.logger.error(f"AWS S3 ClientError generating presigned URL ({error_code}): {e}")
        return None

    except Exception as e:
        app.logger.error(f"Unexpected error generating presigned URL: {e}")
        return None


def upload_file_to_s3(file_path, aws_path, acl="public-read"):
    """
    Upload file to S3 with proper error handling.

    Args:
        file_path (str): Local path to file to upload
        aws_path (str): S3 key/path for the file
        acl (str): Access control level

    Returns:
        str: The original file_path on success

    Raises:
        FileNotFoundError: If local file doesn't exist
        RuntimeError: If S3 upload fails
    """
    from constants import S3_BUCKET_NAME, ErrorMessages

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        s3.upload_file(
            file_path,
            S3_BUCKET_NAME,
            aws_path,
            ExtraArgs={
                "ContentType": "application/pdf",
                "ContentDisposition": "inline",
            },
        )
        app.logger.info(f"Successfully uploaded {file_path} to S3 as {aws_path}")
        return file_path

    except ClientError as e:
        error_code = e.response['Error']['Code']
        app.logger.error(f"AWS S3 ClientError ({error_code}): {e}")
        raise RuntimeError(f"S3 upload failed: {error_code}")

    except Exception as e:
        app.logger.error(f"Unexpected error during S3 upload: {e}")
        raise RuntimeError(ErrorMessages.FILE_UPLOAD_FAILED)

    finally:
        # Clean up local file after upload attempt
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                app.logger.debug(f"Cleaned up local file: {file_path}")
            except OSError as e:
                app.logger.warning(f"Failed to clean up local file {file_path}: {e}")


@celery.task(name="create_memo")
def create_memo(text, dictionary=None):
    from constants import (
        MAX_SUBJECT_LENGTH_FOR_FILENAME,
        RANDOM_ID_LENGTH,
        TEX_EXTENSION,
        PDF_EXTENSION,
        LATEX_TEMP_EXTENSIONS,
        ErrorMessages
    )

    try:
        # Parse memo model with validation
        if dictionary:
            m = memo_model.MemoModel.from_form(dictionary)
        else:
            m = memo_model.MemoModel.from_text(text)

        # Check if parsing failed (returns string error message)
        if isinstance(m, str):
            app.logger.error(f"Memo parsing failed: {m}")
            raise ValueError(ErrorMessages.MEMO_PARSING_ERROR)

        app.logger.debug(m.to_dict())

        # Create memo writer with validation
        try:
            mw = writer.MemoWriter(m)
        except Exception as e:
            app.logger.error(f"Failed to create MemoWriter: {e}")
            raise ValueError(ErrorMessages.INVALID_MEMO_FORMAT)

        # Generate safe filename
        safe_subject = "".join(c for c in m.subject if c.isalnum() or c in (' ', '-', '_')).rstrip()
        temp_name = (
            safe_subject.replace(" ", "_").lower()[:MAX_SUBJECT_LENGTH_FOR_FILENAME]
            + "".join(random.choices("0123456789", k=RANDOM_ID_LENGTH))
            + TEX_EXTENSION
        )
        file_path = os.path.join(app.root_path, temp_name)

        # Write LaTeX file with error handling
        try:
            mw.write(output_file=file_path)
        except Exception as e:
            app.logger.error(f"Failed to write LaTeX file: {e}")
            raise RuntimeError(ErrorMessages.PDF_GENERATION_FAILED)

        # Generate PDF with error handling
        try:
            mw.generate_memo()
        except Exception as e:
            app.logger.error(f"LaTeX compilation failed: {e}")
            raise RuntimeError(ErrorMessages.PDF_GENERATION_FAILED)

        # Check if PDF was generated
        pdf_path = file_path[:-len(TEX_EXTENSION)] + PDF_EXTENSION
        if not os.path.exists(pdf_path):
            app.logger.error(f"PDF not found at expected path: {pdf_path}")
            raise FileNotFoundError(ErrorMessages.PDF_GENERATION_FAILED)

        # Upload to S3 with error handling
        try:
            upload_result = upload_file_to_s3(
                pdf_path,
                temp_name[:-len(TEX_EXTENSION)] + PDF_EXTENSION
            )
            if isinstance(upload_result, Exception):
                raise upload_result
        except Exception as e:
            app.logger.error(f"S3 upload failed: {e}")
            raise RuntimeError(ErrorMessages.FILE_UPLOAD_FAILED)

        # Clean up temporary files
        _cleanup_temp_files(temp_name, LATEX_TEMP_EXTENSIONS)

        return temp_name

    except (ValueError, RuntimeError, FileNotFoundError) as e:
        # Clean up any partial files on error
        if 'temp_name' in locals():
            _cleanup_temp_files(temp_name, LATEX_TEMP_EXTENSIONS + [PDF_EXTENSION])
        raise e
    except Exception as e:
        # Catch-all for unexpected errors
        app.logger.error(f"Unexpected error in create_memo: {e}")
        if 'temp_name' in locals():
            _cleanup_temp_files(temp_name, LATEX_TEMP_EXTENSIONS + [PDF_EXTENSION])
        raise RuntimeError(ErrorMessages.GENERIC_ERROR)


def _cleanup_temp_files(temp_name, file_extensions):
    """Helper function to clean up temporary files."""
    from constants import TEX_EXTENSION

    for extension in file_extensions:
        temp_file = temp_name[:-len(TEX_EXTENSION)] + extension
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                app.logger.debug(f"Cleaned up temp file: {temp_file}")
            except OSError as e:
                app.logger.warning(f"Failed to clean up temp file {temp_file}: {e}")


if os.environ.get("DEVELOPMENT") is None:
    Talisman(app, content_security_policy=None)


def main():
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
