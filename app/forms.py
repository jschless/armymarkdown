from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from db.schema import User

# Removed local_config import - using environment variables instead


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(
                min=6, max=14, message="Username must be between 6 and 14 characters."
            ),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(
                min=6, max=14, message="Password must be between 6 and 14 characters."
            ),
        ],
    )
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only add recaptcha field if it's enabled and configured
        from flask import current_app

        if not current_app.config.get("DISABLE_CAPTCHA") and current_app.config.get(
            "RECAPTCHA_PUBLIC_KEY"
        ):
            self.recaptcha = RecaptchaField()

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                "Username already exists. Please use a different username."
            )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(
                "Email address already has an associated account. Please use a different email address."
            )
