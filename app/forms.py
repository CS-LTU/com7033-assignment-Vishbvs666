from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# -------------------------
# Login Form
# -------------------------
class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)],
    )
    remember_me = BooleanField("Keep me signed in")
    submit = SubmitField("Sign In")


# -------------------------
# Registration Form
# -------------------------
class RegistrationForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")],
    )
    role = SelectField(
        "Role",
        choices=[
            ("admin", "Admin"),
            ("doctor", "Doctor"),
            ("hcp", "Healthcare Professional"),
            ("patient", "Patient"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Register")


# -------------------------
# Reset Password Form (optional)
# -------------------------
class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Reset Password")
