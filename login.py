from flask import render_template, request, url_for, redirect, flash
from urllib.parse import urlsplit
from app import app
from db.schema import User, Document, db
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from forms import LoginForm, RegistrationForm
from armymarkdown import memo_model

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            app.logger.info(
                f"{form.username.data} logged in with wrong username or password"
            )
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user)
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index", example_file="tutorial.Amd")
        app.logger.info(f"{form.username.data} logged in")

        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return url_for("index", example_file="tutorial.Amd")
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        app.logger.info(f"{form.username.data} created an account")
        return render_template("login.html", title="Sign In", form=form)
    return render_template("register.html", title="Register", form=form)


@app.route("/logout")
@login_required
def logout():
    app.logger.info(f"{current_user.username} logged out")
    logout_user()
    return redirect(url_for("index", example_file="tutorial.Amd"))


@app.route("/history")
@login_required
def history():
    user_id = current_user.id
    documents = (
        Document.query.filter_by(user_id=user_id).order_by(Document.id.desc()).all()
    )
    processed_documents = []
    for document in documents:
        try:
            start_index = document.content.find("SUBJECT") + 8  # go to end of subject
            end_index = document.content.find("\n", start_index)
            processed_content = document.content[start_index:end_index].strip(" =")

            processed_documents.append(
                {
                    "id": document.id,
                    "content": processed_content,
                    "preview": document.content[end_index:end_index + 300].strip(),
                }
            )
        except Exception as e:
            app.logger.error("Received following error when trying to render history")
            app.logger.error(e)
    return render_template("history.html", documents=processed_documents)


@app.route("/delete/<int:document_id>")
@login_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    if document.user_id != current_user.id:
        flash("This is not your file, so you can't view it")
        return redirect(url_for("index", example_file="tutorial.Amd"))

    db.session.delete(document)
    db.session.commit()
    flash("Deleted file")
    return redirect(url_for("history"))


@app.route("/<int:document_id>")
@login_required
def get_document(document_id):
    document = Document.query.get_or_404(document_id)
    if document.user_id != current_user.id:
        flash("This is not your file, so you can't view it")
        return redirect(url_for("index", example_file="tutorial.Amd"))

    use_form_editor = request.args.get("form_editor")
    if use_form_editor == "True":
        m = memo_model.MemoModel.from_text(document.content)
        d = m.to_form()
        return render_template("memo_form.html", **d)
    else:
        return render_template("index.html", memo_text=document.content)


def save_document(text):
    if not current_user.is_authenticated:
        return

    user_id = current_user.id

    existing_document = Document.query.filter_by(user_id=user_id, content=text).first()
    if existing_document:
        app.logger.info(
            f"{current_user.username} tried to save a document that already was saved"
        )
        return "Document is already saved."

    from constants import MAX_DOCUMENTS_PER_USER

    num_documents = Document.query.filter_by(user_id=user_id).count()
    removed_oldest = num_documents >= MAX_DOCUMENTS_PER_USER
    if removed_oldest:
        oldest_document = (
            Document.query.filter_by(user_id=user_id)
            .order_by(Document.id.asc())
            .first()
        )
        db.session.delete(oldest_document)
        db.session.commit()
        app.logger.info(
            f"{current_user.username} deleting documents to make room for more saves"
        )
    try:
        new_document = Document(content=text, user_id=user_id)
        db.session.add(new_document)
        db.session.commit()
        app.logger.info(f"{current_user.username} saved document")
        if removed_oldest:
            return "Document saved successfully. Removed oldest document."

        return "Document saved successfully."

    except Exception:
        db.session.rollback()
        return "Document failed to save."
