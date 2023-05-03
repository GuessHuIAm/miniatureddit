from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from passlib.hash import pbkdf2_sha256
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    votes = db.relationship('Vote', backref='user', lazy=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.encrypt(password, rounds=100000, salt_size=16)
        db.session.commit()

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

    def __repr__(self):
        return '<user/{}>'.format(self.username)
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    anonymous = db.Column(db.Boolean, default=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='post', lazy=True)
    votes = db.relationship('Vote', backref='post', lazy='dynamic')
    
    def delete(self):
        self.deleted = True
        db.session.commit()
    

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    anonymous = db.Column(db.Boolean, default=False)
    # parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    # children = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    deleted = db.Column(db.Boolean, default=False)
    votes = db.relationship('Vote', backref='comment', lazy='dynamic')
    
    def delete(self):
        self.deleted = True
        db.session.commit()


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    is_upvote = db.Column(db.Boolean, nullable=False)
