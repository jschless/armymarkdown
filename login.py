from flask import render_template, request, url_for, jsonify, redirect, sessions
from app import app
from db.schema import User, db
from flask_login import LoginManager, login_user, logout_user, login_required
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
            return redirect(
                redirect(url_for("index", example_file="tutorial.Amd"))
            )  # Redirect to login page after account creation

    return render_template("login.html")  # Render login or signup form for GET requests


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index", example_file="tutorial.Amd"))
