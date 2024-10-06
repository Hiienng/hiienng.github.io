# !pip install Flask Flask-SQLAlchemy bcrypt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw, gensalt, checkpw

app = Flask(__name__)

# Setup SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model to store user data in the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Create the database tables (run this once)
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Welcome to the Authentication Service"

if __name__ == '__main__':
    app.run(debug=True)

######################################
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # This will fail if form data is not sent as JSON.
    
    # Handling form data sent via POST request (non-JSON).
    if not data:
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return jsonify({'message': 'Email and password required'}), 400

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'message': 'User already exists'}), 409

        # Hash password and store user
        hashed_password = hashpw(password.encode('utf-8'), gensalt())
        new_user = User(email=email, password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    return jsonify({'message': 'Invalid request'}), 400

######################################
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validate request
    if not data or not 'email' in data or not 'password' in data:
        return jsonify({'message': 'Invalid request'}), 400

    # Check if the user exists
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check if the password matches
    if not checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'message': 'Incorrect password'}), 401

    return jsonify({'message': 'Login successful'}), 200
