from flask import Flask, render_template, request, send_from_directory

from armymarkdown import memo_model, writer

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["GET", "POST"])
def process():
    if request.method == "POST":
        text = request.form["raw_data"]

    m = memo_model.parse_lines(text.split("\n"))
    mw = writer.MemoWriter(m)
    mw.write()
    mw.generate_memo()

    return send_from_directory(
        "/home/joe/Documents/Programming/armymarkdown/",
        "temp_file.pdf",
        as_attachment=True,
    )


if __name__ == "__main__":
    app.run(debug=True)
