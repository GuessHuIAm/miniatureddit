from flask import Flask, render_template, request, redirect, url_for
from models import db, Post
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
    form = PostForm()
    if form.validate_on_submit():
        post = Post(content=form.content.data)
        db.session.add(post)
        db.session.commit()

        node.broadcast_post(post)
        return redirect(url_for('index'))

    posts = Post.query.order_by(Post.upvotes.desc()).all()
    return render_template('index.html', form=form, posts=posts)


@app.route('/upvote/<int:post_id>')
def upvote(post_id):
    post = Post.query.get(post_id)
    if post:
        post.upvotes += 1
        db.session.commit()

        node.broadcast_vote(post_id, True)
    return redirect(url_for('index'))


@app.route('/downvote/<int:post_id>')
def downvote(post_id):
    post = Post.query.get(post_id)
    if post:
        post.downvotes += 1
        db.session.commit()

        node.broadcast_vote(post_id, False)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)