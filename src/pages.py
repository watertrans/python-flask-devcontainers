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
