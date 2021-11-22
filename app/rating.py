from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from sqlalchemy.sql.elements import Null
from werkzeug.urls import url_parse
from app import app, db
from app.forms import EmptyForm, RatingForm
from app.models import User, Post, Contribute, BookRating, ContributorRate
from sqlalchemy import func

def post_rating(id):
    form=RatingForm()
    rate= request.args.get('rating')
    
    if rate is not None:
        rating=BookRating(userid=current_user.id, post_id=id,rate=rate)
        db.session.add(rating)
        db.session.commit()
        flash('Post rated successfully')
    else:
        pass

def post_average_rating(id):
    rates=[]
    book_rating= BookRating.query.filter_by(post_id=id).all()
    for rate in book_rating:
        if rate.rate !=None:
            rates.append(int(rate.rate))
    book_av_rating= sum(rates)/len(rates)
    avg= "{:.0f}".format(book_av_rating)
    return str(avg)

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