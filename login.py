from flask import render_template, request, url_for, jsonify, redirect, sessions
from app import app
from db.schema import User, Document, db
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import logging


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/login", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        app.logger.debug(request.form)
        action = request.form["submit"]

        username = request.form["username"]
        password = request.form["password"]

        if action == "Login":
            # Handle login
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:
                login_user(user)
                return redirect(
                    redirect(url_for("index", example_file="tutorial.Amd"))
                )  # Redirect to the main page after login
            else:
                return "Invalid username or password"  # Handle invalid login

        elif action == "Register":
            # Handle signup
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return "Username already exists! Please choose a different one."
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("index", example_file="tutorial.Amd"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index", example_file="tutorial.Amd"))


@app.route("/history")
@login_required
def history():
    user_id = current_user.id
    documents = Document.query.filter_by(user_id=user_id).all()

    processed_documents = []
    for document in documents:
        start_index = document.content.find("SUBJECT") + 8  # go to end of subject
        end_index = document.content.find("\n", start_index)
        processed_content = document.content[start_index:end_index].strip(" =")

        processed_documents.append({"id": document.id, "content": processed_content})

    return render_template("history.html", documents=processed_documents)


@app.route("/<int:document_id>")
@login_required
def get_document(document_id):
    document = Document.query.get_or_404(document_id)
    return render_template("index.html", memo_text=document.content)


def save_document(text):
    if not current_user.is_authenticated:
        return

    user_id = current_user.id
    try:
        new_document = Document(content=text, user_id=user_id)
        db.session.add(new_document)
        db.session.commit()

        return jsonify({"message": "Document saved successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to save document", "error": str(e)}), 500
