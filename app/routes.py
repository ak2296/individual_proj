from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, current_app,  Markup, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, SearchForm, EditForm,\
    PostEditForm, CompletedForm, RatingForm, AcceptedForm, ResetPasswordRequestForm, ResetPasswordForm, MessageForm
from app.models import User, Post, Contribute, BookRating, Message, ContributorRate, Notification
from app.rating import post_average_rating, post_rating, user_rating, total_rating
from sqlalchemy import func, delete
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    authorate= user_rating(current_user.username)
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user, 
                    title=form.title.data, subtitle=form.subtitle.data, completed=form.completed.data)
        db.session.add(post)
        db.session.commit()
        flash('Your project is now started!','success')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,  
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url, authorate=authorate, total=total_rating)

@app.route('/projects')
@login_required
def projects():
    form_2=RatingForm ()
    authorate= user_rating(current_user.username)
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('projects', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('projects', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Open projects', posts=posts.items, form_2=form_2,
                           next_url=next_url, prev_url=prev_url,authorate=authorate,total=total_rating)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password','danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    authorate= user_rating(username)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form, username=current_user.username,authorate=authorate, total=total_rating)



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    conts= Contribute.query.filter_by(contributor=current_user.username).all()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        for cont in conts:
            cont.contributor=form.username.data
        db.session.commit()
        flash('Your changes have been saved.','info')
        return redirect(url_for('user',username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form, username=current_user.username)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!','danger')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))





@app.route('/contribute/<id>', methods=['GET', 'POST'])
@login_required
def contribute(id):
    ref = Post.query.get(id)
    postauth=User.query.filter_by(username=ref.author.username).first_or_404()
    form = EditForm()
    msgbody='New contribute received for ' + ref.title
    if form.validate_on_submit():
        contribute = Contribute(body=form.post.data, subtitle=form.subtitle.data, contributor=current_user.username, post_id=id)
        msg = Message(author=current_user, recipient=postauth, body=msgbody)
        db.session.add(contribute)
        db.session.add(msg)
        postauth.add_notification('unread_message_count', postauth.new_messages())
        db.session.commit()
        flash('Your contribution to the text have been saved.','success')
        return redirect(url_for('index'))
    return render_template('contribute.html', title='Contribution', user=user,  form=form, id=id , ref=ref)

@app.route('/read_post/<id>', methods=['GET', 'POST'])
@login_required
def read_post(id):
    post=Post.query.get(id)
    form2=AcceptedForm()
    form=CompletedForm()
    
    conts= Contribute.query.filter_by(post_id=post.id).all()
    form2.contributeId.choices=[('')]+[(cont.id) for cont in conts]
    authorate= user_rating(post.author.username)
    if form2.validate_on_submit and form2.accept.data==True :
        cid=form2.contributeId.data
        accepted=Contribute.query.filter_by(id=cid).first()
        accepted.accepted=form2.accept.data
        db.session.commit()
        flash('The Contribution accepted','success')
    elif form2.validate_on_submit and form2.reject.data ==True:
        cid=form2.contributeId.data
        rejected=Contribute.query.filter_by(id=cid).first()
        rejected.accepted=None
        db.session.commit()
        flash('the contribution is rejected.','danger')
        return redirect(url_for('read_post',id=id))
    
    if form.validate_on_submit() and current_user.id==post.user_id:
        post.completed=form.completed.data
        db.session.commit()
        flash('Your project is now published as completed.','success')
        return redirect(url_for('index'))

    return render_template('read_post.html', user=user, post=post, conts=conts,  form2=form2,
                           current_user=current_user,   form=form, authorate=authorate, user_rating=user_rating, total=total_rating)



@app.route('/edit_post/<id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    form = PostEditForm()
    form2= CompletedForm()
    post=Post.query.get(id)
    conts= Contribute.query.filter_by(post_id=post.id).all()
    add=''.join([('Contributed by ')+(cont.contributor.capitalize()+':')+(cont.body) for cont in conts if cont.accepted !=None])
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('index'))
    if form2.validate_on_submit() and current_user.id==post.user_id:
        post.completed=form2.completed.data
        db.session.commit()
        flash('Your project is now published as completed.','success')
        return redirect(url_for('index'))
    form.title.data=post.title
    form.subtitle.data=post.subtitle
    form.body.data=post.body + add
    return render_template('edit_post.html', user=user, post=post, form=form, id=id, form2=form2)




@app.route('/completed')
def completed():
    
    
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(completed=1).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('completed', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('completed', page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('completed.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/rate/<id>', methods=['GET', 'POST'])
def rate(id):
    form=RatingForm()
    books=Post.query.order_by(Post.timestamp.desc())
    rated= BookRating.query.filter_by(userid=current_user.id).all()
    bid=int(id)
    rid=[]
    for r in rated:
            rid.append(int(r.post_id))
    print(rid)
    if form.validate_on_submit():
        if len(rated)<1:
            rate= form.rating.data
            post_rating(id,rate)
        else:
            if bid in rid:
                flash('You have already rated this book','danger')
            else:
                rate= form.rating.data
                post_rating(id,rate)
    
    form.rating.data=post_average_rating(id)
    return render_template('rate.html', user=user, posts=books, form=form, bid=bid,rid=rid)



@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.','info')
        return redirect(url_for('user', username=recipient))
    return render_template('send_message.html', title=('Send Message'),
                           form=form, recipient=recipient)
    
    
@app.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)
    
@app.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
    
