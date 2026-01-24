"""Google OAuth authentication routes."""

import re

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, flash, redirect, url_for
from flask_login import current_user, login_required, login_user

from db.schema import User, db

oauth_bp = Blueprint("oauth", __name__, url_prefix="/auth/google")
oauth = OAuth()


def init_oauth(app):
    """Initialize OAuth with the Flask app."""
    oauth.init_app(app)

    # Register Google OAuth client
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def generate_username(name, email):
    """
    Generate a unique username from Google profile data.

    1. Use Google profile name (sanitized): "John Doe" -> "johndoe"
    2. Fallback to email prefix: "john@gmail.com" -> "john"
    3. Add number if conflict: "johndoe1", "johndoe2"
    4. Minimum 6 characters (pad with "user" if needed)
    """
    # Try name first, then email prefix
    base = name if name else email.split("@")[0]

    # Sanitize: lowercase, alphanumeric only
    base = re.sub(r"[^a-z0-9]", "", base.lower())

    # Ensure minimum 6 characters
    if len(base) < 6:
        base = f"user{base}"
    if len(base) < 6:
        base = base + "user"

    # Truncate to reasonable length
    base = base[:14]

    # Check for conflicts and add number if needed
    username = base
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base[:12]}{counter}"
        counter += 1

    return username


@oauth_bp.route("/login")
def google_login():
    """Redirect to Google for authentication."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Check if Google OAuth is configured
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google sign-in is not configured.")
        return redirect(url_for("login"))

    redirect_uri = url_for("oauth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.route("/callback")
def google_callback():
    """Handle Google OAuth callback."""
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo")

        if not userinfo:
            flash("Failed to get user information from Google.")
            return redirect(url_for("login"))

        google_id = userinfo.get("sub")
        google_email = userinfo.get("email")
        name = userinfo.get("name", "")

        if not google_id or not google_email:
            flash("Failed to get required information from Google.")
            return redirect(url_for("login"))

        # Check if user already exists with this Google ID
        user = User.find_by_google_id(google_id)

        if user:
            # User exists, log them in
            login_user(user, remember=True)
            current_app.logger.info(f"User {user.username} logged in via Google")
            return redirect(url_for("index"))

        # Check if user exists with this email (auto-link)
        user = User.query.filter_by(email=google_email).first()

        if user:
            # Link Google account to existing user
            user.link_google_account(google_id, google_email)
            db.session.commit()
            login_user(user, remember=True)
            current_app.logger.info(
                f"User {user.username} linked Google account and logged in"
            )
            flash("Your Google account has been linked to your existing account.")
            return redirect(url_for("index"))

        # Create new user
        username = generate_username(name, google_email)
        user = User(
            username=username,
            email=google_email,
            google_id=google_id,
            google_email=google_email,
            auth_provider="google",
        )
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=True)
        current_app.logger.info(
            f"New user {username} created via Google OAuth and logged in"
        )
        flash(f"Welcome! Your account has been created with username: {username}")
        return redirect(url_for("index"))

    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {e}")
        flash("An error occurred during Google sign-in. Please try again.")
        return redirect(url_for("login"))


@oauth_bp.route("/link")
@login_required
def google_link():
    """Redirect to Google to link account."""
    if current_user.is_google_linked():
        flash("Your account is already linked to Google.")
        return redirect(url_for("profile"))

    # Check if Google OAuth is configured
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google sign-in is not configured.")
        return redirect(url_for("profile"))

    redirect_uri = url_for("oauth.google_link_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.route("/link/callback")
@login_required
def google_link_callback():
    """Handle Google OAuth callback for account linking."""
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo")

        if not userinfo:
            flash("Failed to get user information from Google.")
            return redirect(url_for("profile"))

        google_id = userinfo.get("sub")
        google_email = userinfo.get("email")

        if not google_id or not google_email:
            flash("Failed to get required information from Google.")
            return redirect(url_for("profile"))

        # Check if this Google account is already linked to another user
        existing_user = User.find_by_google_id(google_id)
        if existing_user and existing_user.id != current_user.id:
            flash("This Google account is already linked to another user.")
            return redirect(url_for("profile"))

        # Link Google account to current user
        current_user.link_google_account(google_id, google_email)
        db.session.commit()

        current_app.logger.info(f"User {current_user.username} linked Google account")
        flash("Your Google account has been successfully linked.")
        return redirect(url_for("profile"))

    except Exception as e:
        current_app.logger.error(f"Google OAuth link error: {e}")
        flash("An error occurred while linking your Google account. Please try again.")
        return redirect(url_for("profile"))


@oauth_bp.route("/unlink", methods=["POST"])
@login_required
def google_unlink():
    """Unlink Google account from user."""
    if not current_user.is_google_linked():
        flash("Your account is not linked to Google.")
        return redirect(url_for("profile"))

    # Prevent unlinking if user has no password (would lock them out)
    if not current_user.can_use_password():
        flash(
            "Please set a password before unlinking your Google account, "
            "otherwise you won't be able to log in."
        )
        return redirect(url_for("profile"))

    current_user.unlink_google_account()
    db.session.commit()

    current_app.logger.info(f"User {current_user.username} unlinked Google account")
    flash("Your Google account has been unlinked.")
    return redirect(url_for("profile"))
