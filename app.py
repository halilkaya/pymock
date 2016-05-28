import os
import json
import datetime
from flask import Flask, abort, request, jsonify, g, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from functools import wraps

# Initialization
app = Flask(__name__)
config = json.load(open('config.json', 'r'))
app.config['SECRET_KEY'] = config['secret_key']
app.config['SQLALCHEMY_DATABASE_URI'] = config['db_connection_string']
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Initial Definitions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
API_NAME = config['api_name']


class User(db.Model):
    """
    User model
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password = db.Column(db.String(255))
    name = db.Column(db.String(40))
    email = db.Column(db.String(120))

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def generate_auth_token(self, expiration=9999):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        serializer = Serializer(app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        user = User.query.get(data['id'])
        return user

class BlogPost(db.Model):
    """
    BlogPost model
    """
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    tags = db.Column(db.Text)
    author = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

def AuthtenticationRequired(func):
    """
    Checks if token is valid to do something
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            abort(403, 'You are forbidden to view this page.')
        user = User.verify_auth_token(token)
        if not user:
            abort(403, 'You are forbidden to view this page.')
        g.user = user
        return func(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    return jsonify({
        "name": API_NAME,
        "status": "OK",
        "code": 200,
        "message": "You must use /v1"
    }), 200

@app.route('/v1')
def v1index():
    return jsonify({
        "name": API_NAME,
        "status": "OK",
        "code": 200
    }), 200

@app.route('/v1/login', methods=['POST'])
@auth.verify_password
def verify_password():
	"""
	Verifies password which is taken from user
	"""
	g.user = None
	if request.json.get('token'):
		user = User.verify_auth_token(request.json.get('token'))
		if not user:
			abort(401, 'Authorization token is invalid or expired.')
		g.user = user
		data = {
			'id': g.user.id,
			'username': g.user.username,
			'name': g.user.name,
			'email': g.user.email,
			'token': g.user.generate_auth_token(9999)
		}
		return jsonify(data), 200
	elif request.json.get('username') and request.json.get('password'):
		user = User.query.filter_by(username=request.json.get('username')).first()
		if not user:
			abort(401, 'Username or password is invalid.')
		is_password_valid = user.verify_password(request.json.get('password'))
		if not user or not is_password_valid:
			abort(401, 'Username or password is invalid.')
		g.user = user
		data = {
			'id': g.user.id,
			'username': g.user.username,
			'name': g.user.name,
			'email': g.user.email,
			'token': g.user.generate_auth_token(9999).decode('utf-8')
		}
		return jsonify(data), 200
	abort(400)


@app.route('/v1/users')
def get_users():
	"""
	Gets all users
	"""
	users = User.query.all()
	data = []
	for user in users:
		data.append({
			'id': user.id,
			'username': user.username,
			'name': user.name,
			'email': user.email
		})
	return jsonify(users=data)

@app.route('/v1/users/<int:id>')
def get_user(id):
	"""
	Gets user by id
	"""
	user = User.query.get(id)
	if not user:
		abort(404, 'User not found.')
	data = {
		'id': user.id,
		'username': user.username,
		'name': user.name,
		'email': user.email
	}
	return jsonify(data)

@app.route('/v1/users', methods=['POST'])
def new_user():
	"""
	Creates a new user
	"""
	if not request.json:
		abort(400)
	username = request.json.get('username')
	password = request.json.get('password')
	name = request.json.get('name')
	email = request.json.get('email')
	if not username or not password or not name or not email:
		abort(400, 'Username, password, name or email is not given.')
	if User.query.filter_by(username=username).first() is not None:
		abort(400, 'Username is already in use.')
	user = User(username=username)
	user.hash_password(password)
	user.name = name
	user.email = email
	db.session.add(user)
	db.session.commit()
	return (jsonify({'username': user.username}), 201,
			{'Location': url_for('get_user', id=user.id, _external=True)})

@app.route('/v1/users/<int:id>', methods=['DELETE'])
@AuthtenticationRequired
def delete_user(id):
    """
    Deletes user
    """
    user = User.query.filter_by(id=id)
    if not user.first():
        abort(404, 'User not found')
    user.delete()
    return jsonify({
        "code": 200,
        "status": "OK",
        "message": "User deleted."
    }), 200

@app.route('/v1/users/<int:id>', methods=['PATCH'])
@AuthtenticationRequired
def update_user(id):
    """
    Updates an existing user
    """
    user = User.query.filter_by(id=id)
    if not user.first():
        abort(404, 'User not found.')
    if not request.json:
        abort(400)
    username = request.json.get('username')
    name = request.json.get('name')
    email = request.json.get('email')
    data = {}
    if username:
        check_user = User.query.filter_by(username=username).first()
        if check_user and check_user.id is not id:
            abort(400, 'Username is already in use.')
        data['username'] = username
    if name:
        data['name'] = name
    if email:
        data['email'] = email
    if not data:
        abort(400)
    user.update(data)
    return jsonify({
        "code": 200,
        "status": "OK",
        "message": "User profile updated."
    }), 200


@app.route('/v1/posts')
def get_blog_posts():
    """
    Gets all blog posts
    """
    posts = BlogPost.query.all()
    data = []
    for post in posts:
        author = User.query.filter_by(id=post.author).first()
        data.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "tags": post.tags,
            "author": author.username,
            "created_at": post.created_at,
            "updated_at": post.updated_at
        })
    return jsonify(posts=data), 200

@app.route('/v1/posts/<int:id>')
def get_blog_post(id):
    """
    Gets blog post
    """
    post = BlogPost.query.filter_by(id=id).first()
    if not post:
        abort(404, 'Blog post not found.')
    author = User.query.filter_by(id=post.author).first()
    return jsonify({
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "tags": post.tags,
        "author": author.username,
        "created_at": post.created_at,
        "updated_at": post.updated_at
    }), 200

@app.route('/v1/posts', methods=['POST'])
@AuthtenticationRequired
def create_blog_post():
    """
    Creates a new blog post
    """
    if not request.json:
        abort(400)
    title = request.json.get('title')
    content = request.json.get('content')
    tags = request.json.get('tags')
    author = g.user
    if not title or not content:
        abort(400)
    post = BlogPost()
    post.title = title
    post.content = content
    if tags:
        post.tags = tags
    post.author = author.id
    db.session.add(post)
    db.session.commit()
    return jsonify({
        "status": "Created",
        "code": 201,
        "message": "Blog post created!"
    }), 201

@app.route('/v1/posts/<int:id>', methods=['DELETE'])
@AuthtenticationRequired
def delete_blog_post(id):
    """
    Deletes blog post
    """
    post = BlogPost.query.filter_by(id=id)
    if not post.first():
        abort(404, 'Blog post not found.')
    if post.first().author is not g.user.id:
        abort(403, 'You are forbidden to delete this blog post.')
    post.delete()
    return jsonify({
        "code": 200,
        "status": "OK",
        "message": "Blog post deleted."
    }), 200

@app.route('/v1/posts/<int:id>', methods=['PATCH'])
@AuthtenticationRequired
def update_blog_post(id):
    """
    Updates an existing blog post
    """
    post = BlogPost.query.filter_by(id=id)
    if not post.first():
        abort(404, 'Blog post not found.')
    if post.first().author is not g.user.id:
        abort(403, 'You are forbidden to update this blog post.')
    if not request.json:
        abort(400)
    title = request.json.get('title')
    content = request.json.get('content')
    tags = request.json.get('tags')
    data = {}
    if title:
        data['title'] = title
    if content:
        data['content'] = content
    if tags:
        data['tags'] = tags
    if not data:
        abort(400)
    data['updated_at'] = datetime.datetime.utcnow()
    post.update(data)
    return jsonify({
        "code": 200,
        "status": "OK",
        "message": "Blog post updated."
    }), 200


@app.errorhandler(400)
def custom400(error):
    return jsonify({
        "name": API_NAME,
        "status": "Bad Request",
        "code": 400,
        "message": error.description
    }), 400

@app.errorhandler(401)
def custom401(error):
    return jsonify({
        "name": API_NAME,
        "status": "Unauthorized",
        "code": 401,
        "message": error.description
    }), 401

@app.errorhandler(403)
def custom403(error):
    return jsonify({
        "name": API_NAME,
        "status": "Forbidden",
        "code": 403,
        "message": error.description
    }), 403

@app.errorhandler(404)
def custom404(error):
    return jsonify({
        "name": API_NAME,
        "status": "Not Found",
        "code": 404,
        "message": error.description
    }), 404

@app.errorhandler(405)
def custom405(error):
    return jsonify({
        "name": API_NAME,
        "status": "Method Not Allowed",
        "code": 405,
        "message": error.description
    }), 405


if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", port=9000, debug=True)
