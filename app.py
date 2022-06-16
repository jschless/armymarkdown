import random
import os

from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    url_for,
    jsonify,
    send_file,
    redirect,
)
from celery import Celery

from armymarkdown import memo_model, writer

app = Flask(__name__)
app.config["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
app.config["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

celery = Celery(
    app.name,
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)
#                 app.config["CELERY_BROKER_URL"])
# celery.conf.update(app.config)

boilerplate_text = open("./memo_template.Amd", "r").read()


@app.route("/")
def index():
    return render_template("index.html", memo_text=boilerplate_text)


@app.route("/process", methods=["POST"])
def process():
    text = request.form["memo_text"]
    print(text)
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
    # print(text.split("\n"))
    task = create_memo.delay(text.split("\n"))
    # mw = writer.MemoWriter(m)
    # mw.write()
    # mw.generate_memo()
    return (
        "Hi, we're waiting for your PDF to be created.",
        200,
        {"Location": url_for("taskstatus", task_id=task.id)},
    )

    return send_from_directory(
        app.root_path,
        "temp_file.pdf",
        as_attachment=True,
    )


@app.route("/status/<task_id>", methods=["POST", "GET"])
def taskstatus(task_id):
    task = create_memo.AsyncResult(task_id)
    print(task.state)
    if task.state == "PENDING":
        # job did not start yet
        response = {"state": task.state, "status": "Pending..."}
    elif task.state == "SUCCESS":
        file_name = task.result[:-4] + ".pdf"
        # move to static folder
        # os.rename(
        #     os.path.join(app.root_path, file_name),
        #     os.path.join(app.root_path, "static", file_name),
        # )
        response = {"state": "SUCCESS", "pdf_file": file_name}
        print("compilation successful, serving test", file_name)
        return jsonify(response)
        return redirect(url_for("results", pdf_name=file_name))
        send_file(
            os.path.join(app.root_path, "static", file_name),
            as_attachment=True,
        )

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
    print(os.path.join(app.root_path, "static", pdf_name))
    return send_file(os.path.join(app.root_path, pdf_name))


@celery.task
def create_memo(lines):
    print("Creating memo")
    m = memo_model.parse_lines(lines)
    mw = writer.MemoWriter(m)

    temp_name = "temp" + "".join(random.choices("0123456789", k=8)) + ".tex"
    mw.write(output_file=temp_name)
    print("writing to latex")
    mw.generate_memo()
    print("memo generated")
    return temp_name


def main():
    app.run(debug=True, threaded=True)


if __name__ == "__main__":
    main()
