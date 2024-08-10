from flask import Blueprint, Config, render_template, redirect, request, session, url_for
from flask import current_app
from forms import *
from werkzeug.datastructures import MultiDict
import inject
import json

from services import AuthService

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


@bp.route("/signin", methods=["GET"])
def signin():
    signin_input = session.get("signin_input", None)
    if signin_input:
        form: SigninForm = SigninForm(MultiDict(json.loads(signin_input)))
        form.validate()
    else:
        form = SigninForm(request.args)
    return render_template("pages/signin.html", form=form)


@bp.route("/signin", methods=["POST"])
@inject.autoparams()
def signin_post(auth_service: AuthService):
    form: SigninForm = SigninForm(request.form)
    if not form.validate():
        session["signin_input"] = json.dumps(request.form)
        return redirect(url_for("pages.signin"))
    session["signin_input"] = None

    current_app.logger.info(auth_service.auth(
        form.email.data or "", form.password.data or ""))

    return redirect(url_for("pages.signin"))


@bp.route("/signup")
def signup():
    return render_template("pages/signup.html")


@bp.route("/reset-password")
def reset_password():
    return render_template("pages/reset_password.html")
