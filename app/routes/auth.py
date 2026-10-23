import re
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        is_json = request.is_json
        data = request.get_json() if is_json else request.form

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        confirm_password = data.get("confirm_password") or ""

        errors = []
        if not name:
            errors.append("Display name is required.")
        if not email or not re.match(EMAIL_REGEX, email):
            errors.append("A valid email address is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if User.query.filter_by(email=email).first():
            errors.append("An account with this email address already exists.")

        if errors:
            if is_json:
                return jsonify({"success": False, "errors": errors}), 400
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html", name=name, email=email)

        # Create user
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)

        if is_json:
            return jsonify({
                "success": True,
                "message": "Account created successfully!",
                "redirect": url_for("dashboard.index")
            }), 201

        flash("Welcome to Smart Expense Tracker!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        is_json = request.is_json
        data = request.get_json() if is_json else request.form

        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        remember = bool(data.get("remember"))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            err_msg = "Invalid email or password. Please try again."
            if is_json:
                return jsonify({"success": False, "message": err_msg}), 401
            flash(err_msg, "danger")
            return render_template("auth/login.html", email=email)

        login_user(user, remember=remember)

        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("dashboard.index")

        if is_json:
            return jsonify({
                "success": True,
                "message": "Logged in successfully!",
                "redirect": next_page
            }), 200

        flash(f"Welcome back, {user.name}!", "success")
        return redirect(next_page)

    return render_template("auth/login.html")


@auth_bp.route("/demo-login", methods=["GET", "POST"])
def demo_login():
    """Provides a one-click login to evaluate the app with sample data."""
    demo_user = User.query.filter_by(email="demo@expensetracker.ai").first()
    if not demo_user:
        demo_user = User(name="Alex Morgan", email="demo@expensetracker.ai")
        demo_user.set_password("DemoPass123!")
        db.session.add(demo_user)
        db.session.commit()

    login_user(demo_user)
    flash("Signed in as Demo User (Alex Morgan)!", "info")
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({"success": True, "message": "Logged out successfully."})
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# API endpoints for direct authentication
@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    return register()


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    return login()


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def api_logout():
    return logout()
