import logging
import os
import random

import boto3
from botocore.exceptions import ClientError
from celery import Celery
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_talisman import Talisman

from armymarkdown import memo_model, writer
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
app.config["DISABLE_CAPTCHA"] = (
    get_optional_env_var("DISABLE_CAPTCHA", "false").lower() == "true"
)

celery = Celery(
    app.name,
    broker=get_required_env_var("REDIS_URL"),
    backend=get_required_env_var("REDIS_URL"),
    broker_connection_retry_on_startup=True,
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
        memo_text=open(os.path.join("./examples", example_file)).read(),
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
            return render_template(
                "index.html", memo_text=request.form.get("memo_text", "")
            )
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
            "status": f"Task failed: {task.info!s}",
            "error": str(task.info),
        }
        app.logger.error(f"Task {task.id} failed: {task.info}")
    elif task.state == "RETRY":
        # Task is being retried
        response = {
            "state": task.state,
            "status": f"Task failed, retrying... ({task.info!s})",
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
            "status": str(task.info)
            if task.info
            else f"Task is {task.state.lower()}...",
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
    if dictionary and isinstance(dictionary, dict):
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

    mw.write(output_file=file_path)

    mw.generate_memo()

    if os.path.exists(file_path[:-4] + ".pdf"):
        upload_file_to_s3(file_path[:-4] + ".pdf", temp_name[:-4] + ".pdf")
    else:
        raise Exception(f"PDF at path {file_path[:-4]}.pdf was not created")

    # clean up temp files after upload to AWS
    file_endings = [
        ".aux",
        ".fdb_latexmk",
        ".fls",
        ".log",
        ".out",
        ".tex",
    ]

    for ending in file_endings:
        temp = temp_name[:-4] + ending
        if os.path.exists(temp):
            os.remove(temp)

    return temp_name


if os.environ.get("DEVELOPMENT") is None:
    Talisman(app, content_security_policy=None)


def main():
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
