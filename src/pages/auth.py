from clients import AssuranceLevel, AuthResult
from decorators import signin_required
from flask import Blueprint, Response, abort, flash, make_response, render_template, redirect, request, session, url_for
from forms import *
from services import AuthService
from utils.web import is_internal_path
from werkzeug.datastructures import MultiDict
import datetime
import inject
import json
import messages

bp = Blueprint("auth", __name__)


@bp.route("/oauth/callback")
@inject.autoparams()
def oauth_callback(auth_service: AuthService):
    """ Handles the postback of the oauth sign-in. """

    error = request.args.get("error", None)
    if error:
        match error:
            case "access_denied":
                flash(messages.FORM_OAUTH_CANCELLED_ALERT, "danger")
            case "temporarily_unavailable":
                flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "danger")
            case _:
                flash(messages.FORM_OAUTH_CONFIGURATION_ERROR_ALERT, "danger")
        return redirect(url_for("auth.signin"))

    code = request.args.get("code", None)
    if not code:
        abort(400)

    auth_result, user_info, session_info = auth_service.exchange_code_for_session(code)
    if auth_result == AuthResult.SUCCESS:
        assert user_info is not None
        assert session_info is not None
        session["user_id"] = user_info.id
        session["access_token"] = session_info.access_token
        session["refresh_token"] = session_info.refresh_token
        session["aal_current"] = user_info.aal_current
        session["aal_next"] = user_info.aal_next
        redirect_to = session.pop("redirect_to", None)
        resp: Response
        if redirect_to:
            resp = make_response(redirect(redirect_to))
        else:
            resp = make_response(redirect(url_for("content.home")))
        return resp
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_AUTH_FAILURE_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    return redirect(url_for("auth.signin"))


@bp.route("/auth/signin", methods=["GET"])
def signin():
    """ Displays the sign-in screen. """

    redirect_to = request.args.get("redirect_to", None)
    if redirect_to and is_internal_path(redirect_to):
        session["redirect_to"] = redirect_to

    signin_input = session.pop("signin_input", None)
    if signin_input:
        form: SigninForm = SigninForm(MultiDict(json.loads(signin_input)))
        form.validate()
    else:
        form = SigninForm(request.args)
        email = session.get("signin_email", "")
        if email:
            form.email.data = email
            form.remember_me.data = False
        email = request.cookies.get("signin_email")
        if email:
            form.email.data = email
            form.remember_me.data = True

    return render_template("auth/signin.html", form=form, localized=messages)


@bp.route("/auth/signin", methods=["POST"])
@inject.autoparams()
def signin_post(auth_service: AuthService):
    """ Handles the postback of the sign-in screen. """
    form: SigninForm = SigninForm(request.form)

    if form.google.data:
        auth_result, auth_url = auth_service.sign_in_with_oauth("google", url_for("auth.oauth_callback", _external=True))
        if auth_result == AuthResult.SUCCESS and auth_url:
            return redirect(auth_url)

    if not form.validate():
        if form.csrf_token.errors:
            flash(messages.FORM_CSRF_ALERT, category="danger")
        else:
            flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
        session["signin_input"] = json.dumps(request.form)
        return redirect(url_for("auth.signin"))

    auth_result, user_info, session_info = auth_service.sign_in_with_password(
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
        redirect_to = session.pop("redirect_to", None)
        resp: Response
        if redirect_to:
            resp = make_response(redirect(redirect_to))
        else:
            resp = make_response(redirect(url_for("content.home")))
        if form.remember_me.data:
            resp.set_cookie("signin_email", form.email.data or "",
                            httponly=True, samesite='Lax', expires=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
        else:
            resp.set_cookie("signin_email", expires=0)
        return resp
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_AUTH_FAILURE_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    session["signin_input"] = json.dumps(request.form)
    return redirect(url_for("auth.signin"))


@bp.route("/auth/verify", methods=["GET"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def verify(auth_service: AuthService):
    """ Displays the two-factor authentication verification screen. """

    redirect_to = request.args.get("redirect_to", None)
    if redirect_to and is_internal_path(redirect_to):
        session["redirect_to"] = redirect_to

    if auth_service.is_two_factor_verified():
        return redirect(url_for("content.home"))

    if not auth_service.has_factor():
        return redirect(url_for("auth.enroll"))

    auth_result, user_info = auth_service.get_user()

    if auth_result != AuthResult.SUCCESS:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")
        return redirect(url_for("auth.verify"))

    assert user_info is not None

    verify_input = session.pop("verify_input", None)
    if verify_input:
        form: VerifyForm = VerifyForm(MultiDict(json.loads(verify_input)))
        for factor in user_info.factors:
            form.factor.choices.append((factor.id, factor.name))  # type: ignore
        form.validate()
    else:
        form = VerifyForm(request.args)
        for factor in user_info.factors:
            form.factor.choices.append((factor.id, factor.name))  # type: ignore

    if len(user_info.factors) == 1:
        form.factor.data = user_info.factors[0].id

    return render_template("auth/verify.html", form=form, localized=messages)


@bp.route("/auth/verify", methods=["POST"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def verify_post(auth_service: AuthService):
    """ Handles the postback of the verification screen. """
    if auth_service.is_two_factor_verified():
        return redirect(url_for("content.home"))

    auth_result, user_info = auth_service.get_user()

    if auth_result != AuthResult.SUCCESS:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")
        return redirect(url_for("auth.verify"))

    assert user_info is not None

    form: VerifyForm = VerifyForm(request.form)
    for factor in user_info.factors:
        form.factor.choices.append((factor.id, factor.name))  # type: ignore

    if not form.validate():
        if form.csrf_token.errors:
            flash(messages.FORM_CSRF_ALERT, category="danger")
        else:
            flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
        session["verify_input"] = json.dumps(request.form)
        return redirect(url_for("auth.verify"))

    auth_result, challenge_info = auth_service.challenge(form.factor.data)

    if auth_result != AuthResult.SUCCESS:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")
        return redirect(url_for("auth.verify"))

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
        redirect_to = session.pop("redirect_to", None)
        if redirect_to:
            return redirect(redirect_to)
        else:
            return redirect(url_for("content.home"))
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_VERIFICATION_FAILURE_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    session["verify_input"] = json.dumps(request.form)
    return redirect(url_for("auth.verify"))


@bp.route("/auth/enroll", methods=["GET"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll(auth_service: AuthService):
    """ Displays the factor enrollment screen. """

    redirect_to = request.args.get("redirect_to", None)
    if redirect_to and is_internal_path(redirect_to):
        session["redirect_to"] = redirect_to

    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("auth.verify", redirect_to=url_for("auth.enroll")))

    enroll_input = session.pop("enroll_input", None)
    if enroll_input:
        form: EnrollForm = EnrollForm(MultiDict(json.loads(enroll_input)))
        form.validate()
    else:
        form = EnrollForm(request.args)
    return render_template("auth/enroll.html", form=form, localized=messages)


@bp.route("/auth/enroll", methods=["POST"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll_post(auth_service: AuthService):
    """ Handles the postback of the enrollment screen. """
    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("auth.verify"))

    form: EnrollForm = EnrollForm(request.form)
    if not form.validate():
        if form.csrf_token.errors:
            flash(messages.FORM_CSRF_ALERT, category="danger")
        else:
            flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
        session["enroll_input"] = json.dumps(request.form)
        return redirect(url_for("auth.enroll"))

    auth_result, factor_info = auth_service.enroll(form.friendly_name.data or "")

    if auth_result == AuthResult.SUCCESS:
        session["enroll_input"] = None
        assert factor_info is not None
        session["factor_id"] = factor_info.id
        session["factor_qr_code"] = factor_info.qr_code
        session["factor_uri"] = factor_info.uri
        return redirect(url_for("auth.enroll_verify"))
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    session["enroll_input"] = json.dumps(request.form)
    return redirect(url_for("auth.enroll"))


@bp.route("/auth/enroll-verify", methods=["GET"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll_verify(auth_service: AuthService):
    """ Displays the verification screen for enrolling a two-factor authentication factor. """
    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("auth.verify"))

    factor_id = session.get("factor_id", None)
    factor_qr_code = session.get("factor_qr_code", None)
    factor_uri = session.get("factor_uri", None)

    if not factor_id or not factor_qr_code or not factor_uri:
        return redirect(url_for("auth.enroll"))

    enroll_verify_input = session.pop("enroll_verify_input", None)
    if enroll_verify_input:
        form: EnrollVerifyForm = EnrollVerifyForm(MultiDict(json.loads(enroll_verify_input)))
        form.validate()
    else:
        form = EnrollVerifyForm(request.args)

    view = {"qr_code": factor_qr_code, "uri": factor_uri}

    return render_template("auth/enroll_verify.html", form=form, view=view, localized=messages)


@bp.route("/auth/enroll-verify", methods=["POST"])
@signin_required(AssuranceLevel.ONE)
@inject.autoparams()
def enroll_verify_post(auth_service: AuthService):
    """ Handles the postback of the verification screen. """
    if auth_service.has_factor() and not auth_service.is_two_factor_verified():
        return redirect(url_for("auth.verify"))

    factor_id = session.get("factor_id", None)

    if not factor_id:
        return redirect(url_for("auth.enroll"))

    form: EnrollVerifyForm = EnrollVerifyForm(request.form)
    if not form.validate():
        if form.csrf_token.errors:
            flash(messages.FORM_CSRF_ALERT, category="danger")
        else:
            flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
        session["enroll_verify_input"] = json.dumps(request.form)
        return redirect(url_for("auth.enroll_verify"))

    auth_result, challenge_info = auth_service.challenge(factor_id)

    if auth_result != AuthResult.SUCCESS:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")
        return redirect(url_for("auth.enroll_verify"))

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
        redirect_to = session.pop("redirect_to", None)
        if redirect_to:
            return redirect(redirect_to)
        else:
            return redirect(url_for("content.home"))
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_VERIFICATION_FAILURE_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    session["enroll_verify_input"] = json.dumps(request.form)
    return redirect(url_for("auth.enroll_verify"))


@bp.route("/auth/signup")
def signup():
    """ Displays the sign-up screen. """

    redirect_to = request.args.get("redirect_to", None)
    if redirect_to and is_internal_path(redirect_to):
        session["redirect_to"] = redirect_to

    signup_input = session.pop("signup_input", None)
    if signup_input:
        form: SignupForm = SignupForm(MultiDict(json.loads(signup_input)))
        form.validate()
    else:
        form = SignupForm(request.args)
    return render_template("auth/signup.html", form=form, localized=messages)


@bp.route("/auth/signup", methods=["POST"])
@inject.autoparams()
def signup_post(auth_service: AuthService):
    """ Handles the postback of the sign-up screen. """
    form: SignupForm = SignupForm(request.form)
    if not form.validate():
        if form.csrf_token.errors:
            flash(messages.FORM_CSRF_ALERT, category="danger")
        else:
            flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
        session["signup_input"] = json.dumps(request.form)
        return redirect(url_for("auth.signup"))

    auth_result, signup_info = auth_service.sign_up(
        form.email.data or "", form.password.data or "")

    if auth_result == AuthResult.CONFIRM_EMAIL:
        session["signup_input"] = None
        session["signin_email"] = form.email.data or ""
        return redirect(url_for("auth.confirm_signup"))
    elif auth_result == AuthResult.SUCCESS:
        session["signup_input"] = None
        session["signin_email"] = form.email.data or ""
        flash(messages.FORM_SIGNUP_SUCCESS_ALERT, "success")
        return redirect(url_for("auth.signin"))
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    session["signup_input"] = json.dumps(request.form)
    return redirect(url_for("auth.signup"))


@bp.route("/auth/confirm-signup", methods=["GET"])
def confirm_signup():
    return render_template("auth/confirm_signup.html", localized=messages)


@bp.route("/auth/reset-password", methods=["GET"])
def reset_password():
    """ Displays the reset password screen. """
    reset_password_input = session.pop("reset_password_input", None)
    if reset_password_input:
        form: ResetPasswordForm = ResetPasswordForm(MultiDict(json.loads(reset_password_input)))
        form.validate()
    else:
        form = ResetPasswordForm(request.args)
    return render_template("auth/reset_password.html", form=form, localized=messages)


@bp.route("/auth/reset-password", methods=["POST"])
@inject.autoparams()
def reset_password_post(auth_service: AuthService):
    """ Handles the postback of the reset password screen. """
    form: ResetPasswordForm = ResetPasswordForm(request.form)
    if not form.validate():
        if form.csrf_token.errors:
            flash(messages.FORM_CSRF_ALERT, category="danger")
        else:
            flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
        session["reset_password_input"] = json.dumps(request.form)
        return redirect(url_for("auth.reset_password"))

    redirect_to = url_for("auth.update_password", _external=True)
    auth_result = auth_service.reset_password(form.email.data or "")

    if auth_result == AuthResult.SUCCESS:
        session["reset_password_input"] = None
        flash(messages.FORM_RESET_PASSWORD_SUCCESS_ALERT, "success")
        return redirect(url_for("auth.reset_password"))
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    session["reset_password_input"] = json.dumps(request.form)
    return redirect(url_for("auth.reset_password"))


@bp.route(rule="/auth/update-password", methods=["GET"])
@inject.autoparams()
def update_password(auth_service: AuthService):
    """ Displays the update password screen. """
    token_hash = request.args.get("token_hash")
    if not token_hash:
        return redirect(url_for(endpoint="auth.reset_password"))
    update_password_input = session.pop("update_password_input", None)
    if update_password_input:
        form: UpdatePasswordForm = UpdatePasswordForm(MultiDict(json.loads(update_password_input)))
        form.validate()
    else:
        form = UpdatePasswordForm(request.args)
        form.token_hash.data = token_hash
    return render_template("auth/update_password.html", form=form, localized=messages)


@bp.route("/auth/update-password", methods=["POST"])
@inject.autoparams()
def update_password_post(auth_service: AuthService):
    """ Handles the postback of the update password screen. """
    form: UpdatePasswordForm = UpdatePasswordForm(request.form)
    if not form.validate():
        if form.csrf_token.errors:
            flash(messages.FORM_CSRF_ALERT, category="danger")
        else:
            flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
        session["update_password_input"] = json.dumps(request.form)
        return redirect(url_for("auth.update_password", token_hash=form.token_hash.data))

    auth_result = auth_service.verify_token_hash_for_recovery(form.token_hash.data or "")
    if auth_result != AuthResult.SUCCESS:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")
        return redirect(url_for(endpoint="auth.reset_password"))

    auth_result = auth_service.update_password(form.password.data or "")

    if auth_result == AuthResult.SUCCESS:
        session["update_password_input"] = None
        flash(messages.FORM_UPDATE_PASSWORD_SUCCESS_ALERT, "success")
        return redirect(url_for("auth.signin"))
    elif auth_result == AuthResult.FAILURE:
        flash(messages.FORM_INVALID_INPUT_ALERT, "warning")
    elif auth_result == AuthResult.UNAVAILABLE:
        flash(messages.FORM_AUTH_UNAVAILABLE_ALERT, "warning")
    else:
        flash(messages.FORM_UNKNOWN_ERROR_ALERT, "danger")

    session["update_password_input"] = json.dumps(request.form)
    return redirect(url_for("auth.update_password", token_hash=form.token_hash.data))


@bp.route(rule="/auth/signout", methods=["GET"])
@inject.autoparams()
def signout(auth_service: AuthService):
    """ Displays the sign-out screen. """

    redirect_to = request.args.get("redirect_to", None)
    auth_service.sign_out()
    session.clear()
    if redirect_to and is_internal_path(redirect_to):
        return redirect(redirect_to)
    else:
        return render_template("auth/signout.html", localized=messages)
