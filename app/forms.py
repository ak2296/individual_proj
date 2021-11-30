from flask_wtf import FlaskForm
from sqlalchemy.orm import defaultload
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, RadioField, SelectField, IntegerField
from wtforms.fields.simple import HiddenField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from flask_ckeditor import CKEditorField
from app.models import User,Contribute
from flask import request


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
            
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
    
class PostForm(FlaskForm):
    title= StringField('Name of Project', validators=[DataRequired(), Length(min=1, max=140)])
    subtitle= StringField('Subtitle', validators=[Length(min=0, max=200)])
    post = CKEditorField('Write your text', validators=[DataRequired()])
    completed=BooleanField("Completed - Check if you want your book to publish as done.")
    submit = SubmitField('Publish')
    
    

class SearchForm(FlaskForm):
    q = StringField(('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)
        
class EditForm(FlaskForm):
    subtitle= StringField('Name for your writing/Chapter', validators=[DataRequired()])
    post= CKEditorField('Add to the text', validators=[DataRequired()])
    submit = SubmitField('Save')
    
class PostEditForm(FlaskForm):
    title= StringField('Name of Project/Book', validators=[DataRequired(), Length(min=1, max=140)])
    subtitle= StringField('Subtitle/Chapter', validators=[DataRequired()])
    body= CKEditorField('Add to the text')
    submit = SubmitField('Save')
    
    
class CompletedForm(FlaskForm):
    completed=BooleanField("Completed - Check if you don't want any contribution to your project",validators=[DataRequired()])
    submit = SubmitField('Publish Book')

class RatingForm(FlaskForm):
    rating = RadioField('', choices=[('1'),('2'), ('3'), ('4'), ('5')], validators=[DataRequired()])
    submit = SubmitField('Submit')
class RemovePost(FlaskForm):
    delete=SubmitField('Delete Post')
    
class AcceptedForm(FlaskForm):
    contributeId=IntegerField('Choose contribute ID:', validators=[DataRequired()], default=[])
    accept = SubmitField('Accept')
    reject = SubmitField('Reject')
