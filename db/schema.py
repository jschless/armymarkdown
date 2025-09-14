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
    password_hash = db.Column(db.String(256), nullable=False)
    documents = db.relationship("Document", backref="user", lazy=True)
    profile = db.relationship("UserProfile", backref="user", uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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
