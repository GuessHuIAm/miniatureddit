from datetime import datetime
from concurrent import futures
from functools import wraps
from multiprocessing import Process
from ipaddress import ip_address
import inquirer
import sys

from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)

from config import *
from forms import LoginForm, PostForm, RegisterForm, CommentForm
from models import Comment, Post, User, Vote, db
from p2p import P2PNode
from gossip import P2PSyncServer

import grpc
import p2psync_pb2 as pb2
import p2psync_pb2_grpc as pb2_grpc

CONFIG_FILE = 'config.py'

def validate_ip(addr):
    """Validates an IP address without noisy ValueError"""
    try:
        if addr == "None":
            return True
        ip_address(addr)
    except:
        raise inquirer.errors.ValidationError("", reason=f"Your input is not an IPV4 or IPV6 address.")
    return True

addr, port = None, None
while True:
    questions = [inquirer.Text('ip', message="What is the IP address of another node in the network?",
                validate=lambda _, x: validate_ip(x)),
                inquirer.Text('port', message="What is the port you want to use to connect to the network?")]

    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
    addr, port = answers['ip'], answers['port']

    # If other node is 'None' provided, then break
    if addr == 'None':
        addr, port = None, None
        break

    # Check to see if the IP address and port represent an active P2PNode
    stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{addr}:{port}'))
    try:
        stub.Connect(request=pb2.Peer(host=HOST, port=str(PORT)))
        break
    except grpc._channel._InactiveRpcError:
        print('Error: The IP address and port you provided does not refer to an active node.')

# Initialize the Flask application
app = Flask(__name__)
app.config.from_pyfile(CONFIG_FILE)

db.init_app(app)
with app.app_context():
    db.create_all()  # Create the database tables for our data models, if they do not exist

# Initialize the P2P node
node = P2PNode(HOST, PORT, addr, port, db.session, app.app_context())

# Setup server infra for the P2PNode
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10)) # 10 threads
pb2_grpc.add_P2PSyncServicer_to_server(P2PSyncServer(), server) # Add service to server
server.add_insecure_port(f'{HOST}:{PORT}')
server.start()
print(f'P2PNode server started on host {HOST} and port {PORT}')

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)


# Route for the homepage, which shows all the posts
@app.route('/', methods=['GET', 'POST'])
def index():
    query = request.args.get('query')
    posts = [{'post': x} for x in Post.query.filter_by(deleted=False).order_by(Post.date_posted.desc()).all()]
    if query:
        posts = [{'post': x} for x in Post.query.filter(Post.title.contains(query) | Post.content.contains(query)).filter_by(deleted=False).order_by(Post.date_posted.desc()).all()]

    # Logic to properly display user upvotes/downvotes
    if current_user.is_authenticated:
        user_id = current_user.id
        for post in posts:
            content = post['post']
            vote_query = content.votes.filter_by(
                user_id=user_id, post_id=content.id
            ).all()
            post['is_upvote'] = vote_query[0].is_upvote if len(vote_query) > 0 else None

    # TODO: Implement post filtering logic/community selection logic
    return render_template(
        'index.html',
        posts=posts,
        logged_in=current_user.is_authenticated,
        query=query)


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
        elif not user.check_password(form.password.data):
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

        node.broadcast_user(user)

        flash('Congratulations, you are now a registered user! You are logged in.')

        login_user(user)

        return redirect(url_for('index'))

    return render_template('register.html', form=form)


# Route for viewing a user's profile, or the current user's profile if no user ID is specified
@app.route('/profile', defaults={'user_id': None})
@app.route('/profile/<int:user_id>')
def profile(user_id):
    if user_id is None:
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            return redirect(url_for('index'))
    user = User.query.get(user_id)

    if current_user.is_authenticated:
        is_current_user = user_id == current_user.id
    else:
        is_current_user = False

    if user:
        posts = Post.query.filter_by(author_id=user_id, deleted=False).order_by(
            Post.date_posted.desc()).all()
        # is_current_user is used to determine whether to show the logout button
        return render_template('profile.html', user=user, posts=posts, is_current_user=is_current_user)
    return redirect(url_for('index'))


# Route for creating a new post
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user, date_posted=datetime.utcnow())
        if form.anonymous.data:
            post.anonymous = True
        db.session.add(post)
        db.session.commit()
        node.broadcast_post(post)
        flash('Your post has been created!')
        return redirect(url_for('index'))
    return render_template('create_post.html', title='Make a Post', form=form)


# Route for creating a new comment
@app.route('/create_comment/<post_id>', methods=['GET', 'POST'])
@app.route('/create_comment/<post_id>/<parent_id>', methods=['GET', 'POST'])
@login_required
def create_comment(post_id, parent_id=None):
    form = CommentForm()
    if form.validate_on_submit():
        if parent_id:
            parent_id = int(parent_id)
            comment = Comment(
                content=form.content.data, author=current_user,
                post_id=post_id, date_posted=datetime.utcnow(), parent_id=parent_id
            )
        else:
            comment = Comment(
                content=form.content.data, author=current_user,
                post_id=post_id, date_posted=datetime.utcnow()
            )
        if form.anonymous.data:
            comment.anonymous = True
        db.session.add(comment)
        db.session.commit()
        node.broadcast_comment(comment)
    return redirect(url_for('post', post_id=post_id))


# Route for deleting a post
@app.route('/delete_post/<post_id>')
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post:
        if post.author_id == current_user.id:
            post.delete()
            db.session.commit()
            node.broadcast_delete_post(post)
            flash('Post deleted.')
        else:
            flash('You cannot delete a post that is not yours.')
    else:
        flash('Post does not exist.')

    # Redirect back to the page the user was on
    return redirect(request.referrer)


# Route for deleting a comment
@app.route('/delete_comment/<comment_id>')
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment:
        if comment.author_id == current_user.id:
            comment.delete()
            db.session.commit()
            flash('Comment deleted.')
        else:
            flash('You cannot delete a comment that is not yours.')
    else:
        flash('Comment does not exist.')

    # Redirect back to the page the user was on
    return redirect(request.referrer)


# Route for upvoting a post or comment
@app.route('/upvote/<is_post>/<int:post_id>/<int:comment_id>/<on_post_page>')
@login_required
def upvote(is_post, post_id, comment_id, on_post_page):
    user_id = current_user.id

    # Converts string to bool, b/c flask routes don't support bool
    is_post = is_post == 'True' # Are we upvoting a post or comment?
    on_post_page = on_post_page == 'True' # Are we on the post page or the homepage?

    # Determine content class and id
    content_class = Post if is_post else Comment
    id = post_id if is_post else comment_id

    # Update upvotes for the content
    content = content_class.query.get(id)
    if content:
        vote_query = \
            content.votes.filter_by(
                user_id=user_id, post_id=id
            ).all() \
            if is_post else \
            content.votes.filter_by(
                user_id=user_id, comment_id=id
            ).all()

        new_vote = Vote(
            user_id = user_id,
            post_id = post_id if is_post else -1,
            comment_id = -1 if is_post else comment_id,
            is_upvote = True
        )

        # If a user has a vote in the database, they have already voted
        has_voted = len(vote_query) > 0
        if has_voted:
            vote = vote_query[0]
            db.session.delete(vote)
            db.session.commit()
            if vote.is_upvote:
                # Remove the vote from the database
                node.broadcast_delete_vote(vote)
            else:
                # Swap from downvote to upvote
                db.session.add(new_vote)
                db.session.commit()
                content.votes.append(new_vote)
                node.broadcast_vote(new_vote)

        # Else, register upvote
        else:
            db.session.add(new_vote)
            db.session.commit()

            content.votes.append(new_vote)
            node.broadcast_vote(new_vote)

        db.session.commit()


    return redirect(url_for('post', post_id=post_id)) if on_post_page else redirect(url_for('index'))


@app.route('/downvote/<is_post>/<int:post_id>/<int:comment_id>/<on_post_page>')
@login_required
def downvote(is_post, post_id, comment_id, on_post_page):
    user_id = current_user.id

    # Converts string to bool, b/c flask routes don't support bool
    is_post = is_post == 'True'
    on_post_page = on_post_page == 'True'

    # Determine content class and id
    content_class = Post if is_post else Comment
    id = post_id if is_post else comment_id

    # Update downvotes for the content
    content = content_class.query.get(id)
    if content:
        vote_query = \
            content.votes.filter_by(
                user_id=user_id, post_id=id
            ).all() \
            if is_post else \
            content.votes.filter_by(
                user_id=user_id, comment_id=id
            ).all()

        new_vote = Vote(
            user_id = user_id,
            post_id = post_id if is_post else -1,
            comment_id = -1 if is_post else comment_id,
            is_upvote = False
        )

        # If a user has voted, either swap from upvote to downvote or
        # remove a downvote
        has_voted = len(vote_query) > 0
        if has_voted:
            vote = vote_query[0]
            db.session.delete(vote)
            db.session.commit()
            if not vote.is_upvote:
                # Remove the vote from the database
                node.broadcast_delete_vote(vote)
            else:
                # Swap from downvote to upvote
                db.session.add(new_vote)
                db.session.commit()
                content.votes.append(new_vote)
                node.broadcast_vote(new_vote)

        # Else, register upvote
        else:
            db.session.add(new_vote)
            db.session.commit()
            content.votes.append(new_vote)
            node.broadcast_vote(new_vote)

        db.session.commit()

    return redirect(url_for('post', post_id=post_id)) if on_post_page else redirect(url_for('index'))


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    def get_comment_tree(comment):
        """Returns a dictionary representing the comment and all its descendants."""
        return {
            'comment': comment,
            'children': [get_comment_tree(child) for child in comment.children],
        }

    def add_is_upvote(comment):
        content = comment['comment']
        vote_query = content.votes.filter_by(user_id=user_id, comment_id=content.id).all()
        is_upvote = vote_query[0].is_upvote if len(vote_query) > 0 else None
        comment['is_upvote'] = is_upvote
        [add_is_upvote(child) for child in comment['children']]


    post = {'post': Post.query.get(post_id)}
    if post['post']:
        root_comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.date_posted.desc()).all()
        comment_trees = [get_comment_tree(comment) for comment in root_comments]

        # Logic to properly display user upvotes/downvotes
        if current_user.is_authenticated:
            user_id = current_user.id
            vote_query = post['post'].votes.filter_by(
                user_id=user_id, post_id=post['post'].id
            ).all()
            post['is_upvote'] = vote_query[0].is_upvote if len(vote_query) > 0 else None
            [add_is_upvote(comment) for comment in comment_trees]

        return render_template('post.html', post=post, form=CommentForm(), comments=comment_trees, logged_in=current_user.is_authenticated)

    return redirect(url_for('index'))


if __name__ == '__main__':
    # Grab a port number from the command line
    p = 5000
    if len(sys.argv) > 1:
        p = int(sys.argv[1])

    app.run(debug=False, port=p)