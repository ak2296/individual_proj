from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import EmptyForm, RatingForm
from app.models import User, Post, Contribute, BookRating, ContributorRate
from sqlalchemy import func

def post_rating(id):
    formR=RatingForm
    post=Post.query.get(id)
    rating=BookRating(userid=current_user.id, post_id=post.id,rate=formR.rating.data)
    db.session.add(rating)
    db.session.commit()
    flash('Post rated successfully')

def post_average_rating(id):
    post=Post.query.get(id)
    book_av_rating= db.session.query(func.avg(BookRating.rate)).filter(BookRating.post_id==post.id).scalar()
    return round(book_av_rating, 1)

def user_rating(id):
    formR=RatingForm
    contribute=Contribute.query.get(id)
    rating=ContributorRate(userid=current_user.id, contributor_id=contribute.contributor_id, rate=formR.rating.data)
    db.session.add(rating)
    db.session.commit()
    flash('Contributor rated successfully')
    
def user_average_rating():
    user_av_rating= db.session.query(func.avg(ContributorRate.rate)).filter(ContributorRate.contributor==Contribute.contributor).scalar()
    return round(user_av_rating, 1)