import random
import os
import sys
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

import login
from login import save_document


@app.after_request
def add_csp(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://www.google.com/recaptcha/api.js https://www.gstatic.com/recaptcha/; "  # Allow scripts from trusted sources
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


@celery.task(name="create_memo")
def create_memo(text, dictionary=None):
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
