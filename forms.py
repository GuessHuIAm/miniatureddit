from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from flask_wtf import FlaskForm
from config import ILLEGAL_CHARS

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    def validate_input(self, username):
        for char in ILLEGAL_CHARS:
            if char in username.data:
                raise ValidationError('Username or password cannot contain the character "{}".'.format(char))
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20), validate_input])
    password = PasswordField('Password', validators=[DataRequired(), validate_input])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign up')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    anonymous = BooleanField('Anonymous')
    submit = SubmitField('Submit')

class CommentForm(FlaskForm):
    content = TextAreaField('Make a Comment', validators=[DataRequired()])
    anonymous = BooleanField('Anonymous')
    submit = SubmitField('Submit')