from flask import Blueprint, render_template
from log_setup import setup_logger

logger = setup_logger(__name__)
bp = Blueprint("pages", __name__)


@bp.route("/")
@bp.route("/home")
def home():
    return render_template("pages/home.html")


@bp.route("/about")
def about():
    return render_template("pages/about.html")


@bp.route("/signin")
def signin():
    return render_template("pages/signin.html")


@bp.route("/signup")
def signup():
    return render_template("pages/signup.html")


@bp.route("/reset-password")
def reset_password():
    return render_template("pages/reset_password.html")
