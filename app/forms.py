'''
===========================================================
StrokeCare Web Application — Secure Software Development
Author: Vishvapriya Sangvikar

Course: COM7033 – MSc Data Science & Artificial Intelligence
Student ID: 2415083
Institution: Leeds Trinity University
Assessment: Assessment 1 – Software Artefact (70%)
AI Statement: Portions of this file were drafted or refined using
    generative AI for planning and editing only,
    as permitted in the module brief.
===========================================================
'''

# app/forms.py

import re

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    SelectField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    EqualTo,
    ValidationError,
)


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
            Length(max=120),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
    )

    remember_me = BooleanField("Keep me signed in")

    # reCAPTCHA field (third-party protection)
    recaptcha = RecaptchaField()

    submit = SubmitField("Sign In")

    def validate(self, extra_validators=None):  # type: ignore[override]
        """
        Override default validate so that in *dev/demo mode* we don’t
        block logins purely because we’re using dummy reCAPTCHA keys.

        - If RECAPTCHA_STRICT = True  -> behave normally (captcha required)
        - If RECAPTCHA_STRICT = False -> ignore recaptcha failures
        """
        from flask import current_app

        strict = current_app.config.get("RECAPTCHA_STRICT", False)

        # Let Flask-WTF do its thing first
        rv = super().validate(extra_validators=extra_validators)

        if rv or strict:
            # Either everything passed OR we are in strict mode
            return rv

        # Not strict and validation failed.
        # If the only errors are on the recaptcha field, we treat it as OK.
        non_captcha_errors = [
            (name, field.errors)
            for name, field in self._fields.items()
            if name != "recaptcha" and field.errors
        ]

        if non_captcha_errors:
            # Some other field (email/password) is wrong → still fail.
            return False

        # Only recaptcha failed → clear its errors and accept form.
        self.recaptcha.errors = []
        return True


# ----------------------------------------
# Registration Form
# ----------------------------------------


class RegistrationForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            validate_any_email,
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            strong_password,
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
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
            strong_password,
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )

    submit = SubmitField("Reset Password")
