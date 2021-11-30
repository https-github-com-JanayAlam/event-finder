from flask_login import current_user
from flask_wtf import FlaskForm
from flaskr import bcrypt
from flaskr.models import User
from wtforms import (DateField, PasswordField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError


class ProfileInfoForm(FlaskForm):
    bio = TextAreaField("Bio", validators=[Length(max=500)],  render_kw={
                        "placeholder": "Write your bio here..."})
    first_name = StringField("First Name", validators=[
        DataRequired(), Length(max=15, min=2)
    ], render_kw={"placeholder": "ex. Alen"})
    last_name = StringField("Last Name", validators=[
        DataRequired(), Length(max=15, min=2)
    ], render_kw={"placeholder": "ex. Walker"})
    dob = DateField("Date of Birth", validators=[
        DataRequired()
    ])
    save = SubmitField("Update")


class VerifyEmailForm(FlaskForm):
    token = StringField("Verification Token", validators=[
        DataRequired(), Length(max=6)
    ], render_kw={"placeholder": "Enter your verification token here..."})
    save = SubmitField("Update")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old Password", validators=[
        DataRequired(), Length(min=6)
    ], render_kw={"placeholder": "Type your old password"})

    new_password = PasswordField("New Password", validators=[
        DataRequired(), Length(min=6)
    ], render_kw={"placeholder": "Type a new password"})

    c_password = PasswordField("Confirm Password", validators=[
        DataRequired(), Length(min=6), EqualTo(
            "new_password", "Confirm password did not matched")
    ], render_kw={"placeholder": "Retype the password"})

    submit = SubmitField("Update")

    def validate_old_password(self, odl_password):
        user = User.query.get(current_user.id)
        if not bcrypt.check_password_hash(user.password, odl_password.data):
            raise ValidationError("Password did not matched.")


class ChangePhoto():
    pass
