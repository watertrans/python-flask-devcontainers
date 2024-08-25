from flask import Blueprint, render_template
from flask import current_app
from forms import *

bp = Blueprint("content", __name__)


@bp.route("/", endpoint="root")
@bp.route("/home")
def home():
    current_app.logger.info("This is sample log")
    return render_template("content/home.html")


@bp.route("/about")
def about():
    return render_template("content/about.html")


@bp.route("/forms")
def forms():
    return render_template("content/forms.html")
