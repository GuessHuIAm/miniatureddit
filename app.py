from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models import db, Post, User, Comment, Vote
from functools import wraps
from forms import PostForm, LoginForm, RegisterForm
from p2p import P2PNode
from config import DB, SECRET_KEY


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Silence the deprecation warning
db.init_app(app)
with app.app_context():
    db.create_all()

node = P2PNode()

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    # Display all the posts
    posts = Post.query.order_by(Post.upvotes.desc()).all()
    return render_template('index.html', posts=posts)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return func(*args, **kwargs)
        else:
            next_url = request.url
            return redirect(url_for('login', next=next_url))
    return wrapper


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

        login_user(user)
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


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

        comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.upvotes.desc()).all()
        return render_template('post.html', post=post, form=form, comments=comments)
    return redirect(url_for('index'))


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user:
        posts = Post.query.filter_by(author_id=user_id).order_by(Post.upvotes.desc()).all()
        return render_template('profile.html', user=user, posts=posts)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)