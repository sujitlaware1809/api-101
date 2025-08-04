from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure DB - Use PostgreSQL in production, SQLite locally
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Production database (PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Local development database (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
db = SQLAlchemy(app)
jwt = JWTManager(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Tweet model
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    username = db.Column(db.String(100), nullable=False)

# Initialize DB
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "🚀 Welcome to Flask Tweet API"

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 409
    
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        token = create_access_token(identity=username)
        return jsonify({'message': 'Login successful', 'token': token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# View all users (auth)
@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = get_jwt_identity()
    users = User.query.all()
    result = [{'id': u.id, 'username': u.username} for u in users]
    return jsonify({'current_user': current_user, 'users': result})

# Post a tweet (auth)
@app.route('/tweet', methods=['POST'])
@jwt_required()
def post_tweet():
    data = request.get_json()
    content = data.get('content')
    
    if not content or len(content) > 280:
        return jsonify({'message': 'Invalid tweet content'}), 400
    
    current_user = get_jwt_identity()
    tweet = Tweet(content=content, username=current_user)
    db.session.add(tweet)
    db.session.commit()
    
    return jsonify({'message': 'Tweet posted successfully'}), 201

# View all tweets
@app.route('/tweets', methods=['GET'])
def get_tweets():
    tweets = Tweet.query.order_by(Tweet.id.desc()).all()
    result = [{'id': t.id, 'user': t.username, 'content': t.content} for t in tweets]
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
