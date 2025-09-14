from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError,
)

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
    recaptcha = RecaptchaField()
    submit = SubmitField("Register")

    def validate_recaptcha(self, field):
        # Only validate recaptcha if it's enabled and configured
        from flask import current_app

        if current_app.config.get("DISABLE_CAPTCHA") or not current_app.config.get(
            "RECAPTCHA_PUBLIC_KEY"
        ):
            return True
        # Let the default RecaptchaField validation handle it
        return super().validate_recaptcha(field)

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


class UserProfileForm(FlaskForm):
    # Personal Information
    full_name = StringField(
        "Full Name",
        validators=[Optional(), Length(max=128)],
        render_kw={"placeholder": "e.g., Sarah M. Johnson"},
    )
    rank = StringField(
        "Rank",
        validators=[Optional(), Length(max=32)],
        render_kw={"placeholder": "e.g., CPT, MAJ, LTC"},
    )
    branch = StringField(
        "Branch",
        validators=[Optional(), Length(max=16)],
        render_kw={"placeholder": "e.g., MI, IN, AR"},
    )
    title = StringField(
        "Title/Position",
        validators=[Optional(), Length(max=128)],
        render_kw={"placeholder": "e.g., Company Commander, S-3"},
    )

    # Organization Information
    organization_name = StringField(
        "Organization Name",
        validators=[Optional(), Length(max=256)],
        render_kw={"placeholder": "e.g., 1st Training Battalion"},
    )
    organization_street = StringField(
        "Street Address",
        validators=[Optional(), Length(max=256)],
        render_kw={"placeholder": "e.g., 1234 Army Drive"},
    )
    organization_city_state_zip = StringField(
        "City, State ZIP",
        validators=[Optional(), Length(max=128)],
        render_kw={"placeholder": "e.g., Fort Liberty, NC 28310"},
    )
    office_symbol = StringField(
        "Office Symbol",
        validators=[Optional(), Length(max=32)],
        render_kw={"placeholder": "e.g., ATZB-CD-E"},
    )

    submit = SubmitField("Save Profile")
