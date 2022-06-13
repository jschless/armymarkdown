from flask import Flask, render_template, request, send_from_directory

from armymarkdown import memo_model, writer

app = Flask(__name__)

boilerplate_text = open("./memo_template.Amd", "r").read()


@app.route("/")
def index():
    return render_template("index.html", memo_text=boilerplate_text)


@app.route("/process", methods=["GET", "POST"])
def process():
    if request.method == "POST":
        text = request.form["memo_text"]

    m = memo_model.parse_lines(text.split("\n"))

    if isinstance(m, str):
        # rudimentary error handling
        print(f"handling error {m}")
        return render_template(
            "index.html", memo_text=f"### {m.strip()} ### \n\n\n {text}"
        )

    mw = writer.MemoWriter(m)
    mw.write()
    mw.generate_memo()

    return send_from_directory(
        app.root_path,
        "temp_file.pdf",
        as_attachment=True,
    )


if __name__ == "__main__":
    app.run(debug=True)
