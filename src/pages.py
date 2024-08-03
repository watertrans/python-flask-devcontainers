from flask import Blueprint, render_template
from flask import current_app

bp = Blueprint("pages", __name__)


@bp.route("/", endpoint="root")
@bp.route("/home")
def home():
    current_app.logger.info("This is sample log")
    return render_template("pages/home.html")


@bp.route("/about")
def about():
    return render_template("pages/about.html")


@bp.route("/forms")
def forms():
    return render_template("pages/forms.html")


@bp.route("/signin")
def signin():
    return render_template("pages/signin.html")


@bp.route("/signup")
def signup():
    return render_template("pages/signup.html")


@bp.route("/reset-password")
def reset_password():
    return render_template("pages/reset_password.html")
