from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from sqlalchemy.sql.elements import Null
from werkzeug.urls import url_parse
from app import app, db
from app.forms import EmptyForm, RatingForm
from app.models import User, Post, Contribute, BookRating, ContributorRate
from sqlalchemy import func

def post_rating(id,rate):
    if rate is not None:
        rating=BookRating(userid=current_user.id, post_id=id,rate=rate)
        db.session.add(rating)
        db.session.commit()
        flash('Post rated successfully','success')
    

def post_average_rating(id):
    rates=[]
    book_rating= BookRating.query.filter_by(post_id=id).all()
    for rate in book_rating:
        if rate.rate !=None:
            rates.append(int(rate.rate))
    if len(rates)>0:
        book_av_rating= sum(rates)/len(rates)
        avg= "{:.0f}".format(book_av_rating)
        return str(avg)



def user_rating(username):
    conts=[]
    contributes=Contribute.query.filter_by(contributor=username).all()
    num=len(contributes)
    for contribute in contributes:
        if contribute.accepted ==1:
            conts.append(contribute)
    acc_len = len(conts)
    if num>0:
        rating=(acc_len*100)/num
        return round(rating,1)
    else:
        return 0

def total_rating(username):
   contributes=Contribute.query.filter_by(contributor=username).all()
   num=len(contributes)
   return num