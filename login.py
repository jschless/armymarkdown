from urllib.parse import urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from app import app
from armymarkdown import memo_model
from db.schema import Document, User, db
from forms import LoginForm, RegistrationForm

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
    documents = get_user_documents(user_id)
    processed_documents = []
    for doc_id, subject, content, _created_at in documents:
        try:
            # Find the end of the subject line to get preview text
            subject_end = content.find("\n", content.find("SUBJECT"))
            preview = (
                content[subject_end : subject_end + 300].strip()
                if subject_end != -1
                else content[:300]
            )

            processed_documents.append(
                {
                    "id": doc_id,
                    "content": subject,
                    "preview": preview,
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

    num_documents = Document.query.filter_by(user_id=user_id).count()
    removed_oldest = num_documents >= 10
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


def get_user_by_username(username):
    """Get user by username for testing purposes."""
    return User.query.filter_by(username=username).first()


def authenticate_user(username, password):
    """Authenticate user with username and password for testing purposes."""
    user = get_user_by_username(username)
    if user is None:
        return False

    # Handle both real User objects and mock dictionary data
    if hasattr(user, "check_password"):
        return user.check_password(password)
    elif isinstance(user, dict) and "password_hash" in user:
        # For testing with mocked user data
        from werkzeug.security import check_password_hash

        return check_password_hash(user["password_hash"], password)

    return False


def get_user_by_email(email):
    """Get user by email for testing purposes."""
    return User.query.filter_by(email=email).first()


def create_user_in_db(username, email, password):
    """Create user in database for testing purposes."""
    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def create_user(username, email, password):
    """Create a new user for testing purposes with success/message return."""
    # Check for existing user
    if get_user_by_username(username):
        return False, "Username already exists"
    if get_user_by_email(email):
        return False, "Email already exists"

    # Create user in database
    if create_user_in_db(username, email, password):
        return True, "User created successfully"
    else:
        return False, "Failed to create user"


def check_password_hash(password_hash, password):
    """Check password hash for testing purposes."""
    from werkzeug.security import check_password_hash as check_hash

    return check_hash(password_hash, password)


def validate_username(username):
    """Validate username for testing purposes."""
    if not username or len(username) < 3:
        return False
    if len(username) > 20:
        return False
    # Allow alphanumeric, underscores, and hyphens based on test
    return all(c.isalnum() or c in "_-" for c in username)


def validate_email(email):
    """Validate email for testing purposes."""
    import re

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return not (not email or not re.match(email_pattern, email))


def validate_password_strength(password):
    """Validate password strength for testing purposes."""
    if not password or len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    return any(c.isdigit() for c in password)


def sanitize_user_input(input_string):
    """Sanitize user input for testing purposes."""
    import html

    if not input_string:
        return ""
    # Basic HTML escaping
    return html.escape(input_string.strip())


def get_db_connection():
    """Get database connection for testing purposes."""
    return db.session


def get_user_documents(user_id):
    """Get all documents for a user for testing purposes."""
    documents = (
        Document.query.filter_by(user_id=user_id).order_by(Document.id.desc()).all()
    )
    result = []
    for doc in documents:
        try:
            # Extract subject from content
            start_index = doc.content.find("SUBJECT") + 8
            end_index = doc.content.find("\n", start_index)
            subject = doc.content[start_index:end_index].strip(" =")

            result.append(
                (doc.id, subject, doc.content, doc.created_at.strftime("%Y-%m-%d"))
            )
        except Exception:
            # If we can't parse the subject, just use the document ID
            result.append(
                (
                    doc.id,
                    f"Document {doc.id}",
                    doc.content,
                    doc.created_at.strftime("%Y-%m-%d"),
                )
            )

    return result
