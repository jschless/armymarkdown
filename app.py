import random
import os

from flask import (
    Flask,
    after_this_request,
    render_template,
    request,
    url_for,
    jsonify,
    send_file,
    redirect,
)
from celery import Celery
import boto3
from armymarkdown import memo_model, writer

app = Flask(__name__)


celery = Celery(
    app.name,
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
)

# celery.conf.update(
#     broker_url=os.environ["REDIS_URL"],
#     result_backemd=os.environ["REDIS_URL"],
# )
boilerplate_text = open("./memo_template.Amd", "r").read()


@app.route("/")
def index():
    return render_template("index.html", memo_text=boilerplate_text)


@app.route("/process", methods=["POST"])
def process():
    text = request.form["memo_text"]
    # m = memo_model.parse_lines(text.split("\n"))

    # if request.form["submit_button"] == "Spellcheck":
    #     admin_errors, body_errors = m.language_check()
    #     error_string = "\n".join(
    #         [f"Error with {k}: {v}" for k, v in admin_errors]
    #     )
    #     error_string += "\n"
    #     error_string += "".join(
    #         [str(err)[str(err).find("\n") :] for err in body_errors]
    #     )
    #     return render_template(
    #         "index.html", memo_text=f"{error_string}\n\n {text}"
    #     )

    # if isinstance(m, str):
    #     # rudimentary error handling
    #     print(f"handling error {m}")
    #     return render_template(
    #         "index.html", memo_text=f"### {m.strip()} ### \n\n\n {text}"
    #     )
    print("submitting task to celery")
    task = create_memo.delay(text.split("\n"))

    return (
        "Hi, we're waiting for your PDF to be created.",
        200,
        {"Location": url_for("taskstatus", task_id=task.id)},
    )


@app.route("/status/<task_id>", methods=["POST", "GET"])
def taskstatus(task_id):
    task = create_memo.AsyncResult(task_id)
    print(f"get request for taskstatus, statis is {task.state}")
    print("redis url", os.environ["REDIS_URL"])
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

    # for end in file_endings:
    #     os.remove(file_path[:-4] + end)

    # file_handle = open(file_path, "r")

    # @after_this_request
    # def remove_file(response):
    #     try:
    #         os.remove(file_path)
    #         file_handle.close()
    #     except Exception as error:
    #         app.logger.error(
    #             "Error removing or closing downloaded file handle", error
    #         )
    #     return response

    return redirect(get_aws_link(pdf_name), code=302)
    return send_file(file_path)


def get_aws_link(file_name):
    return f"https://armymarkdown.s3.us-east-2.amazonaws.com/{file_name}"


def upload_file_to_s3(file, aws_path, acl="public-read"):
    """
    Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
    """
    try:
        s3.upload_file(file, "armymarkdown", aws_path)
    except Exception as e:
        print("Something Happened: ", e)
        return e
    return file


@celery.task
def create_memo(lines):
    print("Creating memo")
    m = memo_model.parse_lines(lines)
    mw = writer.MemoWriter(m)

    temp_name = "temp" + "".join(random.choices("0123456789", k=8)) + ".tex"
    file_path = os.path.join(app.root_path, temp_name)

    mw.write(output_file=file_path)

    mw.generate_memo()
    upload_file_to_s3(file_path[:-4] + ".pdf", temp_name[:-4] + ".pdf")

    return temp_name


def main():
    app.run(debug=True, threaded=True)


if __name__ == "__main__":
    main()
