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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(5000))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
