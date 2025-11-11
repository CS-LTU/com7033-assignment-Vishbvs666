# app/forms.py
from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegisterForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=120)]
    )
    email = EmailField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=255)]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8)]
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    role = SelectField(
        "Role",
        choices=[
            ("admin", "Admin"),
            ("doctor", "Doctor"),
            ("healthcare", "Healthcare"),
            ("patient", "Patient"),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Create account")
