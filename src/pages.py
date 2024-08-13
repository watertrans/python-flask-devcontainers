from clients import AssuranceLevel, AuthResult
from decorators import signin_required
from flask import Blueprint, flash, make_response, render_template, redirect, request, session, url_for
from flask import current_app
from forms import *
from werkzeug.datastructures import MultiDict
import datetime
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
    """ Displays the sign-in screen. """
    signin_input = session.get("signin_input", None)
    if signin_input:
        session["signin_input"] = None
        form: SigninForm = SigninForm(MultiDict(json.loads(signin_input)))
        form.validate()
    else:
        form = SigninForm(request.args)
        email = request.cookies.get("signin_email")
        if email:
            form.email.data = email
            form.remember_me.data = True
    return render_template("pages/signin.html", form=form)


@bp.route("/signin", methods=["POST"])
@inject.autoparams()
def signin_post(auth_service: AuthService):
    """ Handles the postback of the sign-in screen. """
    form: SigninForm = SigninForm(request.form)
    if not form.validate():
        flash("Please check your input and try again.", "warning")
        session["signin_input"] = json.dumps(request.form)
        return redirect(url_for("pages.signin"))

    auth_result, user_info, session_info = auth_service.auth(
        form.email.data or "", form.password.data or "")

    if auth_result == AuthResult.SUCCESS:
        session["signin_input"] = None
        assert user_info is not None
        assert session_info is not None
        session["user_id"] = user_info.id
        session["access_token"] = session_info.access_token
        session["refresh_token"] = session_info.refresh_token
        session["aal_current"] = user_info.aal_current
        session["aal_next"] = user_info.aal_next
        resp = make_response(redirect(url_for("pages.verify")))
        if form.remember_me.data:
            resp.set_cookie("signin_email", form.email.data or "",
                            httponly=True, samesite='Lax', expires=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
        else:
            resp.set_cookie("signin_email", expires=0)
        return resp
    elif auth_result == AuthResult.FAILURE:
        flash("Invalid email or password. Please try again.", "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash("Authentication service is currently unavailable. Please try again later.", "warning")
    else:
        flash("An unknown error occurred. Please try again later.", "danger")

    session["signin_input"] = json.dumps(request.form)
    return redirect(url_for("pages.signin"))


@bp.route("/verify", methods=["GET"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def verify(auth_service: AuthService):
    """ Displays the two-factor authentication verification screen. """
    if auth_service.is_two_factor_verified():
        return redirect(url_for("pages.home"))

    if not auth_service.has_factor():
        return redirect(url_for("pages.enroll"))

    auth_result, user_info = auth_service.get_user()

    if auth_result != AuthResult.SUCCESS:
        flash("An unknown error occurred. Please try again later.", "danger")
        return redirect(url_for("pages.verify"))

    assert user_info is not None

    verify_input = session.get("verify_input", None)
    if verify_input:
        session["verify_input"] = None
        form: VerifyForm = VerifyForm(MultiDict(json.loads(verify_input)))
        for factor in user_info.factors:
            form.factor.choices.append(  # type: ignore
                (factor.id, factor.name))
        form.validate()
    else:
        form = VerifyForm(request.args)
        for factor in user_info.factors:
            form.factor.choices.append(  # type: ignore
                (factor.id, factor.name))

    if len(user_info.factors) == 1:
        form.factor.data = user_info.factors[0].id

    return render_template("pages/verify.html", form=form)


@bp.route("/verify", methods=["POST"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def verify_post(auth_service: AuthService):
    """ Handles the postback of the verification screen. """
    if auth_service.is_two_factor_verified():
        return redirect(url_for("pages.home"))

    auth_result, user_info = auth_service.get_user()

    if auth_result != AuthResult.SUCCESS:
        flash("An unknown error occurred. Please try again later.", "danger")
        return redirect(url_for("pages.verify"))

    assert user_info is not None

    form: VerifyForm = VerifyForm(request.form)
    for factor in user_info.factors:
        form.factor.choices.append(  # type: ignore
            (factor.id, factor.name))

    if not form.validate():
        flash("Please check your input and try again.", "warning")
        session["verify_input"] = json.dumps(request.form)
        return redirect(url_for("pages.verify"))

    auth_result, challenge_info = auth_service.challenge(form.factor.data)

    if auth_result != AuthResult.SUCCESS:
        flash("An unknown error occurred. Please try again later.", "danger")
        return redirect(url_for("pages.verify"))

    assert challenge_info is not None
    auth_result, user_info = auth_service.verify(
        form.factor.data,
        challenge_info.id,
        form.code.data or "")

    if auth_result == AuthResult.SUCCESS:
        session["verify_input"] = None
        assert user_info is not None
        session["user_id"] = user_info.id
        session["aal_current"] = user_info.aal_current
        session["aal_next"] = user_info.aal_next
        return redirect(url_for("pages.home"))
    elif auth_result == AuthResult.FAILURE:
        flash("Invalid verification code. Please try again.", "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash("Authentication service is currently unavailable. Please try again later.", "warning")
    else:
        flash("An unknown error occurred. Please try again later.", "danger")

    session["verify_input"] = json.dumps(request.form)
    return redirect(url_for("pages.verify"))


@bp.route("/enroll", methods=["GET"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll(auth_service: AuthService):
    """ Displays the factor enrollment screen. """
    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("pages.verify"))

    enroll_input = session.get("enroll_input", None)
    if enroll_input:
        form: EnrollForm = EnrollForm(MultiDict(json.loads(enroll_input)))
        form.validate()
    else:
        form = EnrollForm(request.args)
    return render_template("pages/enroll.html", form=form)


@bp.route("/enroll", methods=["POST"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll_post(auth_service: AuthService):
    """ Handles the postback of the enrollment screen. """
    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("pages.verify"))

    form: EnrollForm = EnrollForm(request.form)
    if not form.validate():
        flash("Please check your input and try again.", "warning")
        session["enroll_input"] = json.dumps(request.form)
        return redirect(url_for("pages.enroll"))

    auth_result, factor_info = auth_service.enroll(
        form.friendly_name.data or "")

    if auth_result == AuthResult.SUCCESS:
        session["enroll_input"] = None
        assert factor_info is not None
        session["factor_id"] = factor_info.id
        session["factor_qr_code"] = factor_info.qr_code
        session["factor_uri"] = factor_info.uri
        return redirect(url_for("pages.enroll_verify"))
    elif auth_result == AuthResult.FAILURE:
        flash("Invalid input. Please try again.", "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash("Authentication service is currently unavailable. Please try again later.", "warning")
    else:
        flash("An unknown error occurred. Please try again later.", "danger")

    session["enroll_input"] = json.dumps(request.form)
    return redirect(url_for("pages.enroll"))


@bp.route("/enroll-verify", methods=["GET"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll_verify(auth_service: AuthService):
    """ Displays the verification screen for enrolling a two-factor authentication factor. """
    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("pages.verify"))

    factor_id = session.get("factor_id", None)
    factor_qr_code = session.get("factor_qr_code", None)
    factor_uri = session.get("factor_uri", None)

    if not factor_id or not factor_qr_code or not factor_uri:
        return redirect(url_for("pages.enroll"))

    enroll_verify_input = session.get("enroll_verify_input", None)
    if enroll_verify_input:
        form: EnrollVerifyForm = EnrollVerifyForm(
            MultiDict(json.loads(enroll_verify_input)))
        form.validate()
    else:
        form = EnrollVerifyForm(request.args)

    view = {"qr_code": factor_qr_code, "uri": factor_uri}

    return render_template("pages/enroll_verify.html", form=form, view=view)


@bp.route("/enroll-verify", methods=["POST"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll_verify_post(auth_service: AuthService):
    """ Handles the postback of the verification screen. """
    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("pages.verify"))

    factor_id = session.get("factor_id", None)

    if not factor_id:
        return redirect(url_for("pages.enroll"))

    form: EnrollVerifyForm = EnrollVerifyForm(request.form)
    if not form.validate():
        flash("Please check your input and try again.", "warning")
        session["enroll_verify_input"] = json.dumps(request.form)
        return redirect(url_for("pages.enroll_verify"))

    auth_result, challenge_info = auth_service.challenge(factor_id)

    if auth_result != AuthResult.SUCCESS:
        flash("An unknown error occurred. Please try again later.", "danger")
        return redirect(url_for("pages.enroll_verify"))

    assert challenge_info is not None
    auth_result, user_info = auth_service.verify(
        factor_id,
        challenge_info.id,
        form.code.data or "")

    if auth_result == AuthResult.SUCCESS:
        session["enroll_verify_input"] = None
        assert user_info is not None
        session["user_id"] = user_info.id
        session["aal_current"] = user_info.aal_current
        session["aal_next"] = user_info.aal_next
        session["factor_id"] = None
        session["factor_qr_code"] = None
        session["factor_uri"] = None
        return redirect(url_for("pages.verify"))
    elif auth_result == AuthResult.FAILURE:
        flash("Invalid verification code. Please try again.", "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash("Authentication service is currently unavailable. Please try again later.", "warning")
    else:
        flash("An unknown error occurred. Please try again later.", "danger")

    session["enroll_verify_input"] = json.dumps(request.form)
    return redirect(url_for("pages.enroll_verify"))


@bp.route("/signup")
def signup():
    return render_template("pages/signup.html")


@bp.route("/reset-password")
def reset_password():
    return render_template("pages/reset_password.html")
