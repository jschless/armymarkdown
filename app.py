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

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    config=boto3.session.Config(
        region_name="us-east-2", signature_version="s3v4"
    ),
)

boilerplate_text = open("./memo_template.Amd", "r").read()


@app.route("/")
def index():
    return render_template("index.html", memo_text=boilerplate_text)


@app.route("/spellcheck", methods=["POST"])
def spellcheck():
    task = spellcheck_memo.delay(request.form["memo_text"])
    return (
        "Running Spellcheck",
        200,
        {"Location": url_for("spellcheck_taskstatus", task_id=task.id)},
    )


@app.route("/process", methods=["POST"])
def process():
    task = create_memo.delay(request.form["memo_text"])

    return (
        "Hi, we're waiting for your PDF to be created.",
        200,
        {"Location": url_for("taskstatus", task_id=task.id)},
    )


@app.route("/spellstatus/<task_id>", methods=["POST", "GET"])
def spellcheck_taskstatus(task_id):
    task = spellcheck_memo.AsyncResult(task_id)
    if task.state == "PENDING":
        # job did not start yet
        response = {"state": task.state, "status": "Pending..."}
    elif task.state == "SUCCESS":
        text = task.result
        response = {"state": task.state, "text": text}
        task.forget()
    else:
        # something went wrong in the background job
        response = {
            "state": task.state,
            "status": str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route("/status/<task_id>", methods=["POST", "GET"])
def taskstatus(task_id):
    task = create_memo.AsyncResult(task_id)
    if task.state == "PENDING":
        # job did not start yet
        response = {"state": task.state, "status": "Pending..."}
    elif task.state == "SUCCESS":
        file_name = task.result[:-4] + ".pdf"
        response = {"state": "SUCCESS", "pdf_file": file_name}
        task.forget()  # cleanup redis once done
        # print(f"task successful, pdf is stored at {file_name}")
        return jsonify(response)
    else:
        # something went wrong in the background job
        response = {
            "state": task.state,
            "status": str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route("/results/<pdf_name>", methods=["GET", "POST"])
def results(pdf_name):
    # https://stackoverflow.com/questions/24612366/delete-an-uploaded-file-after-downloading-it-from-flask
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
    # return f"https://armymarkdown.s3.us-east-2.amazonaws.com/{file_name}"


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

    temp_name = "temp" + "".join(random.choices("0123456789", k=8)) + ".tex"
    file_path = os.path.join(app.root_path, temp_name)

    mw.write(output_file=file_path)

    mw.generate_memo()
    upload_file_to_s3(file_path[:-4] + ".pdf", temp_name[:-4] + ".pdf")

    return temp_name


@celery.task(name="spellcheck")
def spellcheck_memo(text):
    m = memo_model.parse_lines(text.split("\n"))

    if isinstance(m, str):
        # rudimentary error handling
        return f"### {m.strip()} ### \n\n\n {text}"

    admin_errors, body_errors = m.language_check()
    error_string = "\n".join([f"Error with {k}: {v}" for k, v in admin_errors])
    error_string += "\n"
    error_string += "".join(
        [str(err)[str(err).find("\n") :] for err in body_errors]
    )

    return f"{error_string}\n\n {text}"


def main():
    app.run(debug=True, threaded=True)


if __name__ == "__main__":
    main()
