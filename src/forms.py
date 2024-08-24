from flask import session
from flask_wtf import Form
from typing import cast
from wtforms import BooleanField, StringField, PasswordField, RadioField, SubmitField, HiddenField
from wtforms.csrf.session import SessionCSRF
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from wtforms.csrf.core import CSRFTokenField
import messages
import os


class CSRFForm(Form):
    csrf_token: CSRFTokenField

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = str.encode(cast(str, os.getenv("SECRET_KEY")))

        @property
        def csrf_context(self):
            return session


class SigninForm(CSRFForm):
    email = StringField(messages.FORM_LABEL_EMAIL, [DataRequired(messages.FORM_FIELD_REQUIRED)], default="")
    password = PasswordField(messages.FORM_LABEL_PASSWORD, validators=[
        DataRequired(messages.FORM_FIELD_REQUIRED),
        Regexp("^[\x21-\x7e]+$", message=messages.FROM_PASSWORD_INVALID_CHARACTERS)], default="")
    remember_me = BooleanField(messages.FORM_LABEL_REMEMBER_ME)
    signin = SubmitField(messages.FORM_LABEL_SIGNIN)
    google = SubmitField(messages.FORM_LABEL_SIGNIN)


class SignupForm(CSRFForm):
    email = StringField(messages.FORM_LABEL_EMAIL, [DataRequired(messages.FORM_FIELD_REQUIRED)], default="")
    password = PasswordField(messages.FORM_LABEL_PASSWORD, validators=[
        DataRequired(messages.FORM_FIELD_REQUIRED),
        Regexp("^[\x21-\x7e]+$", message=messages.FROM_PASSWORD_INVALID_CHARACTERS),
        Length(min=6, message=messages.FORM_PASSWORD_TOO_SHORT),
        Length(max=50, message=messages.FORM_PASSWORD_TOO_LONG)], default="")
    confirm_password = PasswordField(messages.FORM_LABEL_CONFIRM_PASSWORD, validators=[
        DataRequired(messages.FORM_FIELD_REQUIRED),
        EqualTo("password", messages.FORM_PASSWORD_MISMATCH)], default="")
    accept_terms = BooleanField(messages.FORM_LABEL_ACCEPT_TERMS, [DataRequired(messages.FORM_ACCEPT_TERMS_REQUIRED)])
    signin = SubmitField(messages.FORM_LABEL_SIGNIN)


class VerifyForm(CSRFForm):
    factor = RadioField(messages.FORM_LABEL_FACTOR, choices=[], validators=[DataRequired(messages.FORM_FIELD_REQUIRED)])
    code = StringField(messages.FORM_LABEL_VERIFICATION_CODE, [DataRequired(messages.FORM_FIELD_REQUIRED)], default="")
    verify = SubmitField(messages.FORM_LABEL_VERIFY)


class EnrollForm(CSRFForm):
    friendly_name = StringField(
        "Name", [DataRequired(messages.FORM_FIELD_REQUIRED), Length(min=1, max=50, message=messages.FORM_TOO_LONG)], default="")
    enroll = SubmitField(messages.FORM_LABEL_ENROLL)


class EnrollVerifyForm(CSRFForm):
    code = StringField(messages.FORM_LABEL_VERIFICATION_CODE, [DataRequired(messages.FORM_FIELD_REQUIRED)], default="")
    verify = SubmitField(messages.FORM_LABEL_VERIFY)


class ResetPasswordForm(CSRFForm):
    email = StringField(messages.FORM_LABEL_EMAIL, [DataRequired(messages.FORM_FIELD_REQUIRED)], default="")
    submit = SubmitField(messages.FORM_LABEL_SUBMIT)


class UpdatePasswordForm(CSRFForm):
    password = PasswordField(messages.FORM_LABEL_PASSWORD, validators=[
        DataRequired(messages.FORM_FIELD_REQUIRED),
        Regexp("^[\x21-\x7e]+$", message=messages.FROM_PASSWORD_INVALID_CHARACTERS),
        Length(min=6, message=messages.FORM_PASSWORD_TOO_SHORT),
        Length(max=50, message=messages.FORM_PASSWORD_TOO_LONG)], default="")
    confirm_password = PasswordField(messages.FORM_LABEL_CONFIRM_PASSWORD, validators=[
        DataRequired(messages.FORM_FIELD_REQUIRED),
        EqualTo("password", messages.FORM_PASSWORD_MISMATCH)], default="")
    token_hash = HiddenField("token_hash")
    update = SubmitField(messages.FORM_LABEL_SUBMIT)
