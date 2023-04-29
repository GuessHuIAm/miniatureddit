from datetime import datetime
from functools import wraps
from multiprocessing import Process

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)

from config import *
from forms import LoginForm, PostForm, RegisterForm
from models import Comment, Post, User, Vote, db
from p2p import P2PNode

CONFIG_FILE = 'config.py'
SERVER_HIERARCHY = [
    (HOST, PORT),
    (REP_1_HOST, REP_1_PORT),
    (REP_2_HOST, REP_2_PORT)
]


# Initialize the Flask application
app = Flask(__name__)
app.config.from_pyfile(CONFIG_FILE)

db.init_app(app)
with app.app_context():
    db.create_all()  # Create the database tables for our data models, if they do not exist

# Initialize the P2P node
node = P2PNode()

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)

# engine = db.create_engine(SQLALCHEMY_DATABASE_URI)
# conn = engine.connect()

# Route for the homepage, which shows all the posts
@app.route('/', methods=['GET', 'POST'])
def index():
    # Display all the posts
    posts = Post.query.order_by(Post.upvotes.desc()).all()

    # TODO: Implement post filtering logic/community selection logic
    return render_template('index.html', posts=posts)


# This callback is used to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# The wrapper function for the login route
def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return func(*args, **kwargs)
        else:
            next_url = request.url
            return redirect(url_for('login', next=next_url))
    return wrapper


# Route for logging in to the application
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect to the homepage if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Handle the login form submission
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('Username does not exist.')
            return redirect(url_for('login'))
        elif user.check_password(form.password.data):
            flash('Invalid password.')
            return redirect(url_for('login'))

        login_user(user)
        flash('Logged in successfully.')

        return redirect(url_for('index'))

    return render_template('login.html', form=form)


# Route for logging out of the application
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# Route for registering a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect to the homepage if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        query = User.query.filter_by(username=form.username.data).first()
        if query is not None:
            flash('Username already exists.')
            return redirect(url_for('register'))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Congratulations, you are now a registered user! You are logged in.')

        login_user(user)

        return redirect(url_for('index'))

    return render_template('register.html', form=form)


# Route for viewing a user's profile, or the current user's profile if no user ID is specified
@app.route('/profile', defaults={'user_id': None})
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    if user_id is None:
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            return redirect(url_for('index'))
    user = User.query.get(user_id)
    if user:
        posts = Post.query.filter_by(author_id=user_id).order_by(
            Post.upvotes.desc()).all()
        # is_current_user is used to determine whether to show the logout button
        return render_template('profile.html', user=user, posts=posts, is_current_user=user_id == current_user.id)
    return redirect(url_for('index'))


# Route for creating a new post
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    print('INNN HERE')
    form = PostForm()
    if form.validate_on_submit():
        print(form)
        post = Post(title=form.title.data, content=form.content.data, author=current_user, date_posted=datetime.utcnow())
        if form.anonymous.data:
            post.anonymous = True
        db.session.add(post)
        db.session.commit()
        print('Post created')
        flash('Your post has been created!')
        return redirect(url_for('index'))
    return render_template('create_post.html', title='Make a Post', form=form)


# Route for upvoting a post or comment
@app.route('/upvote/<is_post>/<int:id>')
@login_required
def upvote(is_post, id):
    if is_post:
        post = Post.query.get(id)
        if post:
            # TODO: Implement upvote logic
            db.session.commit()
            node.broadcast_vote('post', id, True)
    else:
        comment = Comment.query.get(id)
        if comment:
            # TODO: Implement upvote logic
            db.session.commit()
            node.broadcast_vote('comment', id, True)
    return redirect(url_for('index'))


@app.route('/downvote/<is_post>/<int:id>')
@login_required
def downvote(is_post, id):
    if is_post:
        post = Post.query.get(id)
        if post:
            # TODO: Implement downvote logic
            db.session.commit()
            node.broadcast_vote('post', id, False)
    else:
        comment = Comment.query.get(id)
        if comment:
            # TODO: Implement downvote logic
            db.session.commit()
            node.broadcast_vote('comment', id, False)
    return redirect(url_for('index'))


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get(post_id)
    if post:
        form = PostForm()
        if form.validate_on_submit():
            comment = Comment(content=form.content.data, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('post', post_id=post_id))

        comments = Comment.query.filter_by(
            post_id=post_id).order_by(Comment.upvotes.desc()).all()
        return render_template('post.html', post=post, form=form, comments=comments)
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)

    # primary = Process(target=launch_app, args=(0,))
    # replica_1 = Process(target=launch_app, args=(1,))
    # replica_2 = Process(target=launch_app, args=(2,))

    # primary.start()
    # replica_1.start()
    # replica_2.start()
