from flask import Flask, render_template, request, redirect, url_for
from models import db, Post, User, Comment, Vote
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


@app.route('/', methods=['GET', 'POST'])
def index():
    # Display all the posts
    posts = Post.query.order_by(Post.upvotes.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/upvote/<int:post_id>')
def upvote(post_id):
    post = Post.query.get(post_id)
    if post:
        # TODO: Implement upvote logic
        db.session.commit()

        node.broadcast_vote(post_id, True)
    return redirect(url_for('index'))


@app.route('/downvote/<int:post_id>')
def downvote(post_id):
    post = Post.query.get(post_id)
    if post:
        # TODO: Implement downvote logic
        db.session.commit()

        node.broadcast_vote(post_id, False)
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # TODO: Implement login logic
        pass
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # TODO: Implement register logic
        pass
    return render_template('register.html', form=form)


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


@app.route('/comment/<int:comment_id>')


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)
    if user:
        posts = Post.query.filter_by(author_id=user_id).order_by(Post.upvotes.desc()).all()
        return render_template('profile.html', user=user, posts=posts)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)