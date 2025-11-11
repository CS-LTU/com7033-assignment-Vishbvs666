from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo

ROLE_CHOICES = [
    ("admin", "Admin"),
    ("doctor", "Doctor"),
    ("hcp", "Healthcare Professional"),
    ("patient", "Patient"),
]

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    role = SelectField("Login as", choices=ROLE_CHOICES, validators=[DataRequired()])
    submit = SubmitField("Sign in")

class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=80)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    role = SelectField("I am", choices=ROLE_CHOICES, validators=[DataRequired()])
    submit = SubmitField("Create account")
