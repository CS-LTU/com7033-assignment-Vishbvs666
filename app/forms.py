# app/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    SelectField
)
from wtforms.validators import (
    DataRequired,
    Length,
    EqualTo,
    ValidationError
)

import re


# ----------------------------------------
# Custom Validators (OWASP friendly)
# ----------------------------------------

def validate_any_email(form, field):
    """
    Permissive email validator that allows .test, .local, .nhs.uk, etc.
    Still checks for proper format and prevents junk.
    """
    email = (field.data or "").strip()
    pattern = r"^[^@]+@[^@]+\.[^@]+$"

    if not re.match(pattern, email):
        raise ValidationError("Enter a valid email address.")


def strong_password(form, field):
    """
    OWASP-recommended password strength:
    - at least 8 characters
    - contains uppercase, lowercase, digit
    - contains at least one symbol
    """
    pwd = field.data or ""
    if len(pwd) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", pwd):
        raise ValidationError("Must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", pwd):
        raise ValidationError("Must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", pwd):
        raise ValidationError("Must contain at least one number.")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
        raise ValidationError("Must contain at least one special character.")


# ----------------------------------------
# Login Form
# ----------------------------------------

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            validate_any_email,
            Length(max=120)
        ],
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
    )

    remember_me = BooleanField("Keep me signed in")

    submit = SubmitField("Sign In")


# ----------------------------------------
# Registration Form
# ----------------------------------------

class RegistrationForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            validate_any_email
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            strong_password
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match.")
        ],
    )

    role = SelectField(
        "Role",
        choices=[
            ("admin", "Admin"),
            ("doctor", "Doctor"),
            ("hcp", "Healthcare Professional"),
            ("patient", "Patient"),
        ],
        validators=[DataRequired(message="Please select a role.")],
    )

    submit = SubmitField("Create Account")


# ----------------------------------------
# Reset Password Form
# ----------------------------------------

class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Password is required."),
            strong_password
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match.")
        ],
    )

    submit = SubmitField("Reset Password")
