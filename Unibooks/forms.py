from .models import Users
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired, NumberRange
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import (
    DecimalField, StringField, PasswordField, SubmitField, BooleanField,
    TextAreaField, SelectField, MultipleFileField)


class RegistrationForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    confirm_email = StringField('Confirm Email', validators=[DataRequired(), Email(), EqualTo('email')])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=8, max=50)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'That email is taken. Please Choose a different one')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = Users.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    'That email is taken. Please Choose a different one')


class ItemForm(FlaskForm):
    name = StringField('Item', validators=[DataRequired(), Length(max=100)])
    isbn = StringField('ISBN Number(optional)', validators=[Length(max=13)])
    author = StringField('Author (optional)', validators=[Length(max=50)])
    description = TextAreaField('Description (optional)', validators=[Length(max=400)])
    price = DecimalField('Price', validators=[DataRequired()])
    files = MultipleFileField('Upload item images', validators=[
                              FileAllowed(['jpg', 'png'])])
    item_department = SelectField(
        'Department')
    item_class = SelectField('Course')
    item_category = SelectField('Category')

    submit = SubmitField('Post')
    edit = SubmitField('Edit')


# class EditForm(FlaskForm):
#     name = StringField('Item', validators=[DataRequired()])
#     description = TextAreaField('Description', validators=[DataRequired()])
#     price = DecimalField('Price', validators=[InputRequired()])
#     files = MultipleFileField('Upload item images', validators=[
#                               FileAllowed(['jpg', 'png'])])
#     item_department = SelectField(
#         'Department', validators=[InputRequired()])
#     item_class = SelectField('Class', validators=[InputRequired()])
#     submit = SubmitField('Edit')


class MessageForm(FlaskForm):
    email = StringField('Your Email',
                        validators=[Email()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=150)])
    message_submit = SubmitField('Send')


class PasswordResetForm(FlaskForm):
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=8, max=50)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Reset Password')