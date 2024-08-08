from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


class SigninForm(Form):
    email = StringField('Email', [DataRequired()], default="")
    password = PasswordField('Password', validators=[
        DataRequired(),
        Regexp("^[\x21-\x7e]+$", message="Please enter your password using only single-byte alphanumeric characters and symbols.")], default="")
    signin = SubmitField('Submit')
