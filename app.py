import random
import os
import sys
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    jsonify,
    redirect,
    session,
    flash,
)
from celery import Celery
import logging
import boto3
from botocore.exceptions import ClientError
from armymarkdown import memo_model, writer
from flask_talisman import Talisman
from db.db import init_db

# Load environment variables from .env file
load_dotenv()

def get_required_env_var(var_name):
    """Get required environment variable or raise error if missing."""
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Required environment variable {var_name} is not set")
    return value

def get_optional_env_var(var_name, default=None):
    """Get optional environment variable with default fallback."""
    return os.environ.get(var_name, default)

# Load configuration from environment variables
app = Flask(__name__, static_url_path="/static")
app.secret_key = get_required_env_var("FLASK_SECRET")
app.config["RECAPTCHA_PUBLIC_KEY"] = get_optional_env_var("RECAPTCHA_PUBLIC_KEY")
app.config["RECAPTCHA_PRIVATE_KEY"] = get_optional_env_var("RECAPTCHA_PRIVATE_KEY")
app.config["DISABLE_CAPTCHA"] = get_optional_env_var("DISABLE_CAPTCHA", "false").lower() == "true"

celery = Celery(
    app.name,
    broker=get_required_env_var("REDIS_URL"),
    backend=get_required_env_var("REDIS_URL"),
    broker_connection_retry_on_startup=True,
)

# Configure Celery for production resilience
celery.conf.update(
    # Task execution settings
    task_soft_time_limit=120,    # 2 minutes soft timeout
    task_time_limit=180,         # 3 minutes hard timeout  
    task_acks_late=True,         # Acknowledge after task completion
    worker_prefetch_multiplier=1, # Process one task at a time
    
    # Retry and error handling
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,    # Wait 60s before retry
    task_max_retries=2,             # Max 2 retries
    
    # Result backend settings
    result_expires=3600,            # Results expire after 1 hour
    result_persistent=True,         # Persist results across restarts
    
    # Worker settings for stability
    worker_disable_rate_limits=True,
    worker_send_task_events=True,
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/users.db"


if os.environ.get("DEVELOPMENT") is not None:
    app.debug = True
    app.logger.setLevel(logging.DEBUG)

init_db(app)

s3 = boto3.client(
    "s3",
    aws_access_key_id=get_required_env_var("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=get_required_env_var("AWS_SECRET_ACCESS_KEY"),
    config=boto3.session.Config(region_name="us-east-2", signature_version="s3v4"),
)

import login


@app.after_request
def add_csp(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.google.com/recaptcha/api.js https://www.gstatic.com/recaptcha/; "  # Allow scripts from trusted sources
        "font-src 'self' https://fonts.gstatic.com https://fonts.google.com https://www.gstatic.com data:; "  # Allow data URIs for fonts
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
        try:
            res = login.save_document(text)
            flash(res)
        except Exception as e:
            app.logger.error(f"Error saving document: {e}")
            flash("Error saving document. Please try again.")
        return render_template("index.html", memo_text=text)

    else:
        m = memo_model.MemoModel.from_form(request.form.to_dict())
        if isinstance(m, str):
            # MemoModel.from_form returned an error string
            flash(f"Error creating memo: {m}")
            return redirect(url_for("index"))
        text = m.to_amd()
        try:
            res = login.save_document(text)
            flash(res)
        except Exception as e:
            app.logger.error(f"Error saving document: {e}")
            flash("Error saving document. Please try again.")
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
    try:
        if "SUBJECT" not in request.form:
            # came from the text page
            text = request.form.get("memo_text")
            task = create_memo.delay(text)
        else:
            m = memo_model.MemoModel.from_form(request.form.to_dict())
            if isinstance(m, str):
                # MemoModel.from_form returned an error string
                flash(f"Error creating memo: {m}")
                return redirect(url_for("index"))
            text = m.to_amd()
            task = create_memo.delay("", request.form.to_dict())

        try:
            res = login.save_document(text)
            flash(res)
        except Exception as e:
            app.logger.error(f"Error saving document during processing: {e}")
            flash("Document could not be saved, but processing continues.")

        # memo_errors = check_memo(text)
        # if memo_errors is not None:
        #     return memo_errors, 400
        return (
            "Hi, we're waiting for your PDF to be created.",
            200,
            {"Location": url_for("taskstatus", task_id=task.id)},
        )
    except Exception as e:
        app.logger.error(f"Error processing memo: {e}")
        flash("Error processing memo. Please try again.")
        # Return to appropriate page based on input type
        if "SUBJECT" not in request.form:
            return render_template("index.html", memo_text=request.form.get("memo_text", ""))
        else:
            # Try to reconstruct the form data
            try:
                m = memo_model.MemoModel.from_form(request.form.to_dict())
                if not isinstance(m, str):
                    return render_template("memo_form.html", **m.to_form())
            except:
                pass
            return redirect(url_for("index"))


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
    elif task.state == "FAILURE":
        # Task failed with an exception
        response = {
            "state": task.state,
            "status": f"Task failed: {str(task.info)}",
            "error": str(task.info)
        }
        app.logger.error(f"Task {task.id} failed: {task.info}")
    elif task.state == "RETRY":
        # Task is being retried
        response = {
            "state": task.state,
            "status": f"Task failed, retrying... ({str(task.info)})",
        }
    elif task.state == "REVOKED":
        # Task was revoked/cancelled
        response = {
            "state": task.state,
            "status": "Task was cancelled due to timeout or system issue",
        }
    else:
        # Other states (STARTED, PROGRESS, etc.)
        response = {
            "state": task.state,
            "status": str(task.info) if task.info else f"Task is {task.state.lower()}...",
        }
    return response


@app.route("/status/<task_id>", methods=["POST", "GET"])
def taskstatus(task_id):
    task = create_memo.AsyncResult(task_id)
    return jsonify(process_task(task, lambda res: res[:-4] + ".pdf"))


def get_aws_link(file_name):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
    try:
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "armymarkdown", "Key": file_name},
            ExpiresIn=3600,
        )
    except ClientError as e:
        app.logger.error(f"Something Happened: {e}")
        return None
    return response


def upload_file_to_s3(file, aws_path, acl="public-read"):
    """
    Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
    """
    ret_val = None
    try:
        s3.upload_file(
            file,
            "armymarkdown",
            aws_path,
            ExtraArgs={
                "ContentType": "application/pdf",
                "ContentDisposition": "inline",
            },
        )
        ret_val = file
    except Exception as e:
        app.logger.error(f"Something Happened: {e}")
        ret_val = e
    finally:
        # delete file after uploads
        if os.path.exists(file):
            os.remove(file)
        return ret_val


@celery.task(name="create_memo", bind=True)
def create_memo(self, text, dictionary=None):
    """Create memo PDF with comprehensive error handling and timeout protection."""
    temp_name = None
    file_path = None
    
    try:
        if dictionary:
            m = memo_model.MemoModel.from_form(dictionary)
        else:
            m = memo_model.MemoModel.from_text(text)

        app.logger.debug(m.to_dict())
        mw = writer.MemoWriter(m)

        temp_name = (
            m.subject.replace(" ", "_").lower()[:15]
            + "".join(random.choices("0123456789", k=4))
            + ".tex"
        )
        file_path = os.path.join(app.root_path, temp_name)

        # Write LaTeX file
        app.logger.info(f"Writing LaTeX file: {file_path}")
        mw.write(output_file=file_path)

        # Generate PDF with timeout protection
        app.logger.info(f"Starting LaTeX compilation for: {temp_name}")
        mw.generate_memo()
        app.logger.info(f"LaTeX compilation completed for: {temp_name}")

        pdf_path = file_path[:-4] + ".pdf"
        if os.path.exists(pdf_path):
            app.logger.info(f"PDF created successfully: {pdf_path}")
            upload_file_to_s3(pdf_path, temp_name[:-4] + ".pdf")
            app.logger.info(f"PDF uploaded to S3: {temp_name[:-4]}.pdf")
        else:
            raise Exception(f"PDF was not created at expected path: {pdf_path}")

    except Exception as e:
        error_msg = f"Memo creation failed: {str(e)}"
        app.logger.error(error_msg)
        
        # Cleanup any partial files on error
        if file_path:
            cleanup_temp_files(file_path, temp_name)
            
        # Re-raise with more context
        raise self.retry(exc=Exception(error_msg), countdown=60, max_retries=2)

    # Clean up temp files after successful upload to AWS
    cleanup_temp_files(file_path, temp_name)
    return temp_name


def cleanup_temp_files(file_path, temp_name):
    """Clean up temporary LaTeX compilation files."""
    if not file_path or not temp_name:
        return
        
    file_endings = [
        ".aux",
        ".fdb_latexmk", 
        ".fls",
        ".log",
        ".out",
        ".tex",
        ".synctex.gz"  # Added this common LaTeX artifact
    ]

    base_name = temp_name[:-4] if temp_name.endswith('.tex') else temp_name
    
    for ending in file_endings:
        temp_file = os.path.join(os.path.dirname(file_path), base_name + ending)
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                app.logger.debug(f"Cleaned up temp file: {temp_file}")
        except Exception as e:
            app.logger.warning(f"Failed to cleanup {temp_file}: {e}")


if os.environ.get("DEVELOPMENT") is None:
    Talisman(app, content_security_policy=None)


def main():
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
