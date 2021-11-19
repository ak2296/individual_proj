from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, SearchForm, EditForm,\
    PostEditForm, CompletedForm, RatingForm, AcceptedForm
from app.models import User, Post, Contribute, BookRating
from app.rating import post_average_rating, post_rating
from sqlalchemy import func, delete

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
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user, 
                    title=form.title.data, subtitle=form.subtitle.data, completed=form.completed.data)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
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
                           prev_url=prev_url)

@app.route('/explore')
@login_required
def explore():
    form_2=RatingForm ()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Open projects', posts=posts.items, form_2=form_2,
                           next_url=next_url, prev_url=prev_url)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
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
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

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
            flash('You cannot follow yourself!')
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



@app.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)
    
    
@app.route('/contribute/<id>', methods=['GET', 'POST'])
@login_required
def contribute(id):
    ref = Post.query.get(id)
    form = EditForm()
    if form.validate_on_submit():
        contribute = Contribute(body=form.post.data, subtitle=form.subtitle.data, contributor=current_user.username, post_id=id)
        db.session.add(contribute)
        db.session.commit()
        flash('Your contribution to the text have been saved.')
        return redirect(url_for('index'))
    return render_template('contribute.html', title='Contribution', user=user,  form=form, id=id , ref=ref)

@app.route('/read_post/<id>', methods=['GET', 'POST'])
@login_required
def read_post(id):
    post=Post.query.get(id)
    form2=AcceptedForm()
    form=CompletedForm()
    conts= Contribute.query.filter_by(post_id=post.id)
    
    if form2.validate_on_submit and form2.accept.data==True :
        cid=form2.contributeId.data
        conId=[]
        for con in conts:
            conId.append(con.id)
        if cid in conId:
            accepted=Contribute.query.filter_by(id=cid).first()
            accepted.accepted=form2.accept.data
            db.session.commit()
            flash('The Contribution accepted','seccess')
    elif form2.validate_on_submit and form2.reject.data ==True:
        cid=form2.contributeId.data
        conId=[]
        for con in conts:
            conId.append(con.id)
        if cid in conId:
            rejected=Contribute.query.filter_by(id=cid).first()
            db.session.delete(rejected)
            db.session.commit()
            flash('the contribution is deleted.','danger')
            return redirect(url_for('read_post/<id>'))
        else:
            flash('Wrong entry. Choose the right number','danger')
    elif form.validate_on_submit() and current_user.id==post.user_id:
        post.completed=form.completed.data
        db.session.commit()
        flash('Your project is now published as completed.','seccess')
        return redirect(url_for('index'))

    return render_template('read_post.html', user=user, post=post, conts=conts,  form2=form2,
                           current_user=current_user,   form=form)



@app.route('/edit_post/<id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    form = PostEditForm()
    post=Post.query.get(id)
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('index'))
    form.title.data=post.title
    form.subtitle.data=post.subtitle
    form.body.data=post.body
    return render_template('edit_post.html', user=user, post=post, form=form, id=id)




@app.route('/completed')
def completed():
    
    books=Post.query.order_by(Post.timestamp.desc())
    page = request.args.get('page', 1, type=int)
    posts = books.paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('completed.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/rate/<id>', methods=['GET', 'POST'])
def rate(id):
    form=RatingForm()
    books=Post.query.order_by(Post.timestamp.desc())
    post_rating(id)
    form.rating.data=post_average_rating(id)
    return render_template('rate.html', user=user, posts=books, form=form, bid=int(id))
