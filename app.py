import random
import os
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    jsonify,
    redirect,
)
from celery import Celery
import boto3
from botocore.exceptions import ClientError
from armymarkdown import memo_model, writer

app = Flask(__name__)

if "REDIS_URL" not in os.environ:
    # set os.environ from local_config
    from local_config import config

    for key, val in config.items():
        os.environ[key] = val

celery = Celery(
    app.name,
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
)

celery.conf.broker_pool_limit = 0
celery.conf.redis_max_connections = 20  # free heroku tier limit


s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    config=boto3.session.Config(region_name="us-east-2", signature_version="s3v4"),
)


@app.route("/")
def home():
    return redirect(url_for("index", example_file="tutorial.Amd"))


@app.route("/<example_file>")
def index(example_file="./tutorial.Amd"):
    text = ""
    if example_file not in os.listdir("./examples"):
        example_file = "./tutorial.Amd"

    example_file = os.path.join("./examples", example_file)
    text = open(example_file, "r").read()

    return render_template("index.html", memo_text=text)


def check_memo(text):
    m = memo_model.parse_lines(text.split("\n"))

    if isinstance(m, str):
        # rudimentary error handling
        return m.strip()

    errors = m.language_check()
    if len(errors) > 0:
        return "\n".join([f"Error with {k}: {v}" for k, v in errors])

    return None


@app.route("/process_files", methods=["POST"])
def process_files():
    print("Processing files", request.files)
    task_ids = []
    for uploaded_file in request.files.getlist("file"):
        text = uploaded_file.read().decode()
        task = create_memo.delay(text)
        task_ids.append(task.id)
    return (",".join(task_ids), 200, {"File_list": task_ids})


@app.route("/process", methods=["POST"])
def process():
    text = request.form["memo_text"]
    memo_errors = check_memo(text)
    if memo_errors is not None:
        return memo_errors, 400

    task = create_memo.delay(text)
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


@app.route("/results/<pdf_name>", methods=["GET", "POST"])
def results(pdf_name):
    file_endings = [
        ".aux",
        ".fdb_latexmk",
        ".fls",
        ".log",
        ".out",
        ".tex",
    ]
    file_path = os.path.join(app.root_path, pdf_name)

    for end in file_endings:
        if os.path.exists(file_path[:-4] + end):
            os.remove(file_path[:-4] + end)

    return redirect(get_aws_link(pdf_name), code=302)


def get_aws_link(file_name):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html

    try:
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "armymarkdown", "Key": file_name},
            ExpiresIn=3600,
        )
    except ClientError as e:
        print(e)
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
                "ContentDisposition": "attachment",
            },
        )
        ret_val = file
    except Exception as e:
        print("Something Happened: ", e)
        ret_val = e
    finally:
        # delete file after uploads
        if os.path.exists(file):
            os.remove(file)
        return ret_val


@celery.task(name="create_memo")
def create_memo(text):
    m = memo_model.parse_lines(text.split("\n"))
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

    return temp_name


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
