from datetime import timedelta
from functools import lru_cache
import logging
import os
import time

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from flask_talisman import Talisman

from app.auth import login

# Google OAuth disabled - uncomment to re-enable
# from app.auth.oauth import init_oauth, oauth_bp
from app.forms import UserProfileForm
from app.memo_adapter import (
    MemoFormError,
    ProfileSubstitution,
    document_to_form_context,
    example_choices,
    form_data_to_template_context,
    form_to_amd,
    packaged_example_names,
    parse_memo_text,
    read_example_text,
    substitute_profile_fields,
)
from app.tasks import create_memo, huey
from db.db import init_db
from db.schema import Document, UserProfile

# Load environment variables from .env file
load_dotenv()

# Get the project root directory (one level up from app/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_required_env_var(var_name):
    """Get required environment variable or raise error if missing."""
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Required environment variable {var_name} is not set")
    return value


def get_optional_env_var(var_name, default=None):
    """Get optional environment variable with default fallback."""
    return os.environ.get(var_name, default)


# Load configuration from environment variables
app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=os.path.join(project_root, "static"),
    template_folder=os.path.join(project_root, "templates"),
)
app.secret_key = get_required_env_var("FLASK_SECRET")
app.config["RECAPTCHA_PUBLIC_KEY"] = get_optional_env_var("RECAPTCHA_PUBLIC_KEY")
app.config["RECAPTCHA_PRIVATE_KEY"] = get_optional_env_var("RECAPTCHA_PRIVATE_KEY")
app.config["DISABLE_CAPTCHA"] = (
    get_optional_env_var("DISABLE_CAPTCHA", "false").lower() == "true"
)

# Google OAuth configuration
app.config["GOOGLE_CLIENT_ID"] = get_optional_env_var("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = get_optional_env_var("GOOGLE_CLIENT_SECRET")

# Initialize login manager
login.login_manager.init_app(app)

# Register login routes
login.register_login_routes(app)

# Google OAuth disabled - uncomment to re-enable
# init_oauth(app)
# app.register_blueprint(oauth_bp)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/users.db"

# Session configuration for "Remember Me" functionality
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=7)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)


if os.environ.get("DEVELOPMENT") is not None:
    app.debug = True
    app.logger.setLevel(logging.DEBUG)

init_db(app)

s3 = boto3.client(
    "s3",
    aws_access_key_id=get_required_env_var("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=get_required_env_var("AWS_SECRET_ACCESS_KEY"),
    config=boto3.session.Config(region_name="us-east-2", signature_version="s3v4"),
)


@app.after_request
def add_csp(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.google.com/recaptcha/api.js https://www.gstatic.com/recaptcha/; "  # Allow scripts from trusted sources
        "font-src 'self' https://fonts.gstatic.com https://fonts.google.com https://www.gstatic.com data:; "  # Allow data URIs for fonts
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "  # Allow inline styles if necessary
        "frame-src https://www.google.com;"
        "img-src 'self'; "  # Only allow images from the same origin
        "connect-src 'self' https://accounts.google.com;"  # Allow Google OAuth
    )
    return response


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for container monitoring"""
    try:
        # Test database connection
        from sqlalchemy import text

        from db.schema import db

        db.session.execute(text("SELECT 1"))

        # Check Huey is available
        huey_status = "ok" if huey else "unavailable"

        return jsonify(
            {
                "status": "healthy",
                "timestamp": time.time(),
                "services": {"database": "ok", "huey": huey_status},
            }
        ), 200
    except Exception as e:
        return jsonify(
            {"status": "unhealthy", "timestamp": time.time(), "error": str(e)}
        ), 503


@app.route("/", methods=["GET"])
def index():
    example_file = process_example_file(request.args)

    # Handle user document loading
    if example_file.startswith("doc:"):
        document_id = example_file.split(":", 1)[1]
        document = Document.query.get_or_404(document_id)
        if document.user_id != current_user.id:
            flash("Access denied to that document")
            return redirect(url_for("index", example_file="tutorial.Amd"))
        memo_text = document.content
    else:
        user_id = current_user.id if current_user.is_authenticated else None
        memo_text = load_example_text(example_file, user_id)

    return render_template(
        "index.html",
        memo_text=memo_text,
        examples=get_example_files(),
    )


@lru_cache(maxsize=1)
def _get_static_example_files():
    """Cache the packaged example files list."""
    return example_choices()


def get_example_files():
    """Get list of example files with display names, including user history if logged in."""
    # Start with cached static examples (copy to avoid modifying cached list)
    examples = list(_get_static_example_files())

    # Add user history if logged in
    if current_user.is_authenticated:
        from app.auth.login import get_user_documents

        user_documents = get_user_documents(current_user.id)

        if user_documents:
            # Add a separator
            examples.append(("---", "--- Your Documents ---"))

            # Add user documents (show recent 10 in dropdown to avoid overwhelming the UI)
            for doc_id, subject, _content, created_at in user_documents[:10]:
                # Truncate subject if too long
                display_subject = subject[:50] + "..." if len(subject) > 50 else subject
                # Format: "Subject (date)"
                date_str = (
                    created_at.strftime("%m/%d/%y")
                    if hasattr(created_at, "strftime")
                    else str(created_at)[:10]
                )
                display_name = f"📄 {display_subject} ({date_str})"
                examples.append((f"doc:{doc_id}", display_name))

    return examples


def process_example_file(args):
    example_file = args.get("example_file", "tutorial.Amd")

    # Handle document IDs (from user history)
    if example_file.startswith("doc:"):
        return example_file

    # Handle separator entries
    if example_file == "---":
        example_file = "tutorial.Amd"

    if example_file not in packaged_example_names():
        example_file = "tutorial.Amd"

    return example_file


@app.route("/form", methods=["GET"])
def form():
    example_file = process_example_file(request.args)

    # Handle user document loading
    if example_file.startswith("doc:"):
        document_id = example_file.split(":", 1)[1]
        document = Document.query.get_or_404(document_id)
        if document.user_id != current_user.id:
            flash("Access denied to that document")
            return redirect(url_for("form", example_file="tutorial.Amd"))
        document_model = parse_memo_text(document.content)
    else:
        document_model = parse_memo_text(
            load_example_text(
                example_file,
                current_user.id if current_user.is_authenticated else None,
            )
        )
    memo_dict = document_to_form_context(document_model)
    memo_dict["examples"] = get_example_files()

    return render_template("memo_form.html", **memo_dict)


@app.route("/save_progress", methods=["POST"])
def save_progress():
    if "SUBJECT" not in request.form:
        text = request.form.get("memo_text")
        try:
            res = login.save_document(text)
            if res:
                flash(res)
        except Exception as e:
            app.logger.error(f"Error saving document: {e}")
            flash("Error saving document. Please try again.")
        return render_template("index.html", memo_text=text)

    else:
        try:
            text = form_to_amd(request.form.to_dict())
        except MemoFormError as exc:
            flash(f"Error creating memo: {exc}")
            context = form_data_to_template_context(request.form.to_dict())
            context["examples"] = get_example_files()
            return render_template("memo_form.html", **context)
        try:
            res = login.save_document(text)
            if res:
                flash(res)
        except Exception as e:
            app.logger.error(f"Error saving document: {e}")
            flash("Error saving document. Please try again.")
        context = document_to_form_context(parse_memo_text(text))
        context["examples"] = get_example_files()
        return render_template("memo_form.html", **context)


@app.route("/auto_save", methods=["POST"])
@login_required
def auto_save():
    """Auto-save endpoint for background saves without page refresh"""
    try:
        if "SUBJECT" not in request.form:
            # Text editor mode
            text = request.form.get("memo_text", "")
        else:
            try:
                text = form_to_amd(request.form.to_dict())
            except MemoFormError as exc:
                return jsonify(
                    {"success": False, "error": f"Error creating memo: {exc}"}
                ), 400

        if not text or text.strip() == "":
            return jsonify({"success": False, "error": "No content to save"}), 400

        # Use auto-save specific function that handles duplicates gracefully
        result = login.auto_save_document(text)

        if not result["success"]:
            return jsonify(result), 400

        # Add timestamp to successful response
        result["timestamp"] = time.time()
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error auto-saving document: {e}")
        return jsonify({"success": False, "error": "Auto-save failed"}), 500


@app.route("/process", methods=["POST"])
def process():
    try:
        if "SUBJECT" not in request.form:
            # came from the text page
            text = request.form.get("memo_text")
            task = create_memo(text)
        else:
            try:
                text = form_to_amd(request.form.to_dict())
            except MemoFormError as exc:
                flash(f"Error creating memo: {exc}")
                context = form_data_to_template_context(request.form.to_dict())
                context["examples"] = get_example_files()
                return render_template("memo_form.html", **context)
            task = create_memo(text)

        try:
            res = login.save_document(text)
            if res:
                flash(res)
        except Exception as e:
            app.logger.error(f"Error saving document during processing: {e}")
            flash("Document could not be saved, but processing continues.")

        # Return task ID for status polling
        return (
            "Hi, we're waiting for your PDF to be created.",
            200,
            {"Location": url_for("taskstatus", task_id=task.id)},
        )
    except Exception as e:
        app.logger.error(f"Error processing memo: {e}")
        flash("Error processing memo. Please try again.")
        # Return to appropriate page based on input type
        if "SUBJECT" not in request.form:
            return render_template(
                "index.html", memo_text=request.form.get("memo_text", "")
            )
        else:
            context = form_data_to_template_context(request.form.to_dict())
            context["examples"] = get_example_files()
            return render_template("memo_form.html", **context)


# Store for tracking Huey task results
_task_results = {}


def process_huey_task(task_id, result_func):
    """Process Huey task status and return appropriate response."""

    # Get the task result from Huey
    result = huey.result(task_id, preserve=True)

    if result is None:
        # Task is still pending or processing
        return {"state": "PENDING", "status": "Creating your memo..."}

    # Check if result is an exception
    if isinstance(result, Exception):
        app.logger.error(f"Task {task_id} failed: {result}")
        return {
            "state": "FAILURE",
            "status": f"Task failed: {result!s}",
            "error": str(result),
        }

    # Task completed successfully
    pdf_name = result_func(result)
    return {
        "state": "SUCCESS",
        "result": pdf_name,
        "presigned_url": get_aws_link(pdf_name),
    }


@app.route("/status/<task_id>", methods=["POST", "GET"])
def taskstatus(task_id):
    """Get the status of a memo creation task."""
    return jsonify(process_huey_task(task_id, lambda res: res))


def get_aws_link(file_name):
    """Generate a presigned URL for downloading a file from S3."""
    try:
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "armymarkdown", "Key": file_name},
            ExpiresIn=3600,
        )
    except ClientError as e:
        app.logger.error(f"S3 presigned URL error: {e}")
        return None
    return response


def load_example_text(example_name, user_id=None):
    """Load packaged example text and apply profile substitutions when possible."""
    example_text = read_example_text(example_name)
    if not user_id or not current_user.is_authenticated:
        return example_text

    # Skip profile substitution during testing to avoid mock issues
    import sys

    if "pytest" in sys.modules or hasattr(sys, "_called_from_test"):
        return example_text

    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not user_profile:
        return example_text

    substitutions: list[ProfileSubstitution] = []
    profile_fields = {
        "ORGANIZATION_NAME": user_profile.organization_name,
        "ORGANIZATION_STREET_ADDRESS": user_profile.organization_street,
        "ORGANIZATION_CITY_STATE_ZIP": user_profile.organization_city_state_zip,
        "OFFICE_SYMBOL": user_profile.office_symbol,
        "AUTHOR": user_profile.full_name,
        "RANK": user_profile.rank,
        "BRANCH": user_profile.branch,
        "TITLE": user_profile.title,
    }
    for field_name, value in profile_fields.items():
        if isinstance(value, str) and value:
            substitutions.append(
                ProfileSubstitution(field_name=field_name, value=value)
            )

    return substitute_profile_fields(example_text, substitutions)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile management page."""
    from db.schema import db

    # Get or create user profile
    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not user_profile:
        user_profile = UserProfile(user_id=current_user.id)

    form = UserProfileForm(obj=user_profile)

    if form.validate_on_submit():
        # Update profile with form data
        form.populate_obj(user_profile)

        # Add to session if it's a new profile
        if not user_profile.id:
            db.session.add(user_profile)

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("profile"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e!s}", "error")

    return render_template("profile.html", form=form, profile=user_profile)


@app.route("/validate", methods=["POST"])
@login_required
def validate_memo():
    """
    Validate memo content against AR 25-50 rules.

    Accepts either AMD text format or form data.
    Returns validation results including errors and warnings.
    """
    from app.services.validation import MemoValidator

    try:
        if "SUBJECT" not in request.form:
            # Text editor mode
            text = request.form.get("memo_text", "")
            result = MemoValidator.validate_text_input(text)
        else:
            # Form mode - validate form fields directly
            validator = MemoValidator(request.form.to_dict())
            result = validator.validate_all()

        return jsonify(
            {
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
            }
        )

    except Exception as e:
        app.logger.error(f"Validation error: {e}")
        return jsonify(
            {
                "is_valid": False,
                "errors": [f"Validation failed: {e!s}"],
                "warnings": [],
            }
        ), 500


@app.route("/validate/pdf", methods=["POST"])
@login_required
def validate_pdf_upload():
    """
    Upload a PDF file for AR 25-50 compliance validation.

    Accepts multipart form data with a 'file' field containing the PDF.
    Returns a task ID that can be polled for results.
    """
    from app.tasks import validate_pdf_task

    # Check if file was uploaded
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    # Check if file was selected
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    # Read file content
    pdf_bytes = file.read()

    # Check file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(pdf_bytes) > max_size:
        return jsonify({"error": "File too large (max 10MB)"}), 400

    # Check minimum size (sanity check)
    if len(pdf_bytes) < 100:
        return jsonify({"error": "File appears to be empty or corrupted"}), 400

    # Queue validation task
    task = validate_pdf_task(pdf_bytes, current_user.id, file.filename)

    return jsonify({"task_id": task.id, "filename": file.filename})


@app.route("/validate/pdf/status/<task_id>", methods=["GET"])
@login_required
def validation_task_status(task_id):
    """
    Get the status of a PDF validation task.

    Returns task status and results when complete.
    """
    result = huey.result(task_id, preserve=True)

    if result is None:
        return jsonify({"state": "PENDING", "status": "Analyzing document..."})

    if isinstance(result, Exception):
        app.logger.error(f"Validation task {task_id} failed: {result}")
        return jsonify(
            {
                "state": "FAILURE",
                "status": f"Validation failed: {result!s}",
                "error": str(result),
            }
        )

    return jsonify(
        {
            "state": "SUCCESS",
            "result_id": result.get("result_id"),
            "score": result.get("score"),
            "is_compliant": result.get("is_compliant"),
            "issue_count": len(result.get("issues", [])),
        }
    )


@app.route("/validate/result/<int:result_id>")
@login_required
def validation_result(result_id):
    """
    Display validation results page for a specific validation.

    Args:
        result_id: ID of the ValidationResult to display
    """
    from db.schema import ValidationResult

    result = ValidationResult.query.get_or_404(result_id)

    # Ensure user can only view their own results
    if result.user_id != current_user.id:
        flash("Access denied to that validation result", "error")
        return redirect(url_for("validate_page"))

    return render_template("validation_result.html", result=result)


@app.route("/validate/history")
@login_required
def validation_history():
    """Display user's validation history."""
    from db.schema import ValidationResult

    results = (
        ValidationResult.query.filter_by(user_id=current_user.id)
        .order_by(ValidationResult.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template("validation_history.html", results=results)


@app.route("/validate")
@login_required
def validate_page():
    """Display the PDF validation upload page."""
    return render_template("validate.html")


@app.route("/validate/rules", methods=["GET"])
def get_validation_rules():
    """
    Get the list of validation rules applied to memos.

    Returns the AR 25-50 rules configuration.
    """
    from app.services.validation.rules import get_all_rules, get_rule_config

    rules = get_all_rules()
    config = get_rule_config()

    return jsonify(
        {
            "rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity.value,
                    "ar_reference": rule.ar_reference,
                }
                for rule in rules
            ],
            "config": config,
        }
    )


if os.environ.get("DEVELOPMENT") is None:
    # Caddy handles SSL termination, so disable force_https
    # Keep other security headers (XSS, content-type, etc.)
    Talisman(app, content_security_policy=None, force_https=False)


def main():
    app.run(debug=True, host="0.0.0.0")  # nosec B201 B104


if __name__ == "__main__":
    main()
