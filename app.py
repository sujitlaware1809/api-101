from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Replace securely in production
db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    username = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "🚀 Flask Tweet API: CRUD with JWT"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username, password = data.get('username'), data.get('password')
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 409
    db.session.add(User(username=username, password=password))
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username'), password=data.get('password')).first()
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401
    token = create_access_token(identity=user.username)
    return jsonify({'message': 'Login successful', 'token': token}), 200

@app.route('/tweet', methods=['POST'])
@jwt_required()
def post_tweet():
    content = request.get_json().get('content')
    if not content or len(content) > 280:
        return jsonify({'message': 'Invalid tweet content'}), 400
    tweet = Tweet(content=content, username=get_jwt_identity())
    db.session.add(tweet)
    db.session.commit()
    return jsonify({'message': 'Tweet posted successfully', 'tweet_id': tweet.id}), 201

@app.route('/tweets', methods=['GET'])
def get_tweets():
    tweets = Tweet.query.order_by(Tweet.id.desc()).all()
    return jsonify([{'id': t.id, 'user': t.username, 'content': t.content} for t in tweets])

@app.route('/tweet/<int:id>', methods=['PUT'])
@jwt_required()
def update_tweet(id):
    tweet = Tweet.query.get(id)
    if not tweet:
        return jsonify({'message': 'Tweet not found'}), 404
    if tweet.username != get_jwt_identity():
        return jsonify({'message': 'Unauthorized'}), 403
    content = request.get_json().get('content')
    if not content or len(content) > 280:
        return jsonify({'message': 'Invalid tweet content'}), 400
    tweet.content = content
    db.session.commit()
    return jsonify({'message': 'Tweet updated successfully'}), 200

@app.route('/tweet/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_tweet(id):
    tweet = Tweet.query.get(id)
    if not tweet:
        return jsonify({'message': 'Tweet not found'}), 404
    if tweet.username != get_jwt_identity():
        return jsonify({'message': 'Unauthorized'}), 403
    db.session.delete(tweet)
    db.session.commit()
    return jsonify({'message': 'Tweet deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
