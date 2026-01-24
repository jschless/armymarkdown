from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import check_password_hash, generate_password_hash


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(
        db.String(256), nullable=True
    )  # Nullable for OAuth-only users

    # Google OAuth fields
    google_id = db.Column(db.String(128), unique=True, nullable=True, index=True)
    google_email = db.Column(db.String(128), nullable=True)
    auth_provider = db.Column(
        db.String(32), default="local"
    )  # 'local', 'google', 'both'

    documents = db.relationship("Document", backref="user", lazy=True)
    profile = db.relationship("UserProfile", backref="user", uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def can_use_password(self):
        """Returns True if user has a password set."""
        return self.password_hash is not None

    def is_google_linked(self):
        """Returns True if Google account is linked."""
        return self.google_id is not None

    def link_google_account(self, google_id, google_email):
        """Link Google account to this user."""
        self.google_id = google_id
        self.google_email = google_email
        if self.auth_provider == "local":
            self.auth_provider = "both"
        elif self.auth_provider is None:
            self.auth_provider = "google"

    def unlink_google_account(self):
        """Unlink Google account from this user."""
        self.google_id = None
        self.google_email = None
        if self.auth_provider == "both":
            self.auth_provider = "local"

    @classmethod
    def find_by_google_id(cls, google_id):
        """Find user by Google ID."""
        return cls.query.filter_by(google_id=google_id).first()


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Personal Information
    full_name = db.Column(db.String(128))  # e.g., "Sarah M. Johnson"
    rank = db.Column(db.String(32))  # e.g., "CPT"
    branch = db.Column(db.String(16))  # e.g., "MI"
    title = db.Column(db.String(128))  # e.g., "Company Commander"

    # Organization Information
    organization_name = db.Column(db.String(256))  # e.g., "1st Training Battalion"
    organization_street = db.Column(db.String(256))  # e.g., "1234 Army Drive"
    organization_city_state_zip = db.Column(
        db.String(128)
    )  # e.g., "Fort Liberty, NC 28310"
    office_symbol = db.Column(db.String(32))  # e.g., "ATZB-CD-E"

    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(5000))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class ValidationResult(db.Model):
    """Stores PDF validation results for AR 25-50 compliance checking."""

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # PDF identification
    pdf_hash = db.Column(db.String(64))  # SHA-256 hash of PDF content
    pdf_filename = db.Column(db.String(256))

    # Validation status
    is_compliant = db.Column(db.Boolean, default=False)
    compliance_score = db.Column(db.Float)  # 0.0 to 1.0

    # Detailed results stored as JSON
    issues = db.Column(db.JSON)  # List of issues found
    pdf_metadata = db.Column(db.JSON)  # Extracted PDF metadata

    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    user = db.relationship("User", backref=db.backref("validations", lazy=True))
    document = db.relationship("Document", backref=db.backref("validations", lazy=True))
