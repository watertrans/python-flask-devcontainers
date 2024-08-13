from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, RadioField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


class SigninForm(Form):
    email = StringField("Email", [DataRequired()], default="")
    password = PasswordField("Password", validators=[
        DataRequired(),
        Regexp("^[\x21-\x7e]+$", message="Please enter your password using only single-byte alphanumeric characters and symbols.")], default="")
    remember_me = BooleanField("Remember me")
    signin = SubmitField("Submit")


class VerifyForm(Form):
    factor = RadioField('Factor', choices=[], validators=[DataRequired()])
    code = StringField("Verification code", [DataRequired()], default="")
    verify = SubmitField("Verify")


class EnrollForm(Form):
    friendly_name = StringField(
        "Name", [DataRequired(), Length(min=1, max=50)], default="", )
    enroll = SubmitField("Enroll")


class EnrollVerifyForm(Form):
    code = StringField("Verification code", [DataRequired()], default="")
    verify = SubmitField("Verify")
