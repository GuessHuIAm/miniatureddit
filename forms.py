from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class PostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    # Implement login form fields
    pass


class RegisterForm(FlaskForm):
    # Implement registration form fields
    pass
