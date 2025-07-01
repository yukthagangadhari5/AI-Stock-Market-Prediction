import webbrowser
from threading import Timer
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


# Define paths for your models
MODEL_PATHS = {
    'AMZN': r"C:/Users/legen/OneDrive/Documents/Desktop/yukta/instance/model/modelamzn.py",
    'AAPL': r"C:/Users/legen/OneDrive/Documents/Desktop/yukta/instance/model/modelapple.py",
    'TSLA': r"C:/Users/legen/OneDrive/Documents/Desktop/yukta/instance/model/modeltesla.py",
    'MSFT': r"C:/Users/legen/OneDrive/Documents/Desktop/yukta/instance/model/modelmsft.py",
    'GOOGL': r"C:/Users/legen/OneDrive/Documents/Desktop/yukta/instance/model/modelgoogle.py",
}

@app.route('/model', methods=['GET'])
def model():
    company = request.args.get('company')
    if company not in MODEL_PATHS:
        return jsonify({'error': 'Invalid company'}), 400

    model_path = MODEL_PATHS[company]

    # Ensure the file exists
    if not os.path.exists(model_path):
        return jsonify({'error': f'Model for {company} not found'}), 404

    try:
        # Dynamically load and execute the model script
        with open(model_path, 'r') as model_file:
            exec(model_file.read(), globals())  # This executes the script

        # Replace `prediction` and `dates` with values returned by the model
        # Ensure the model script generates variables like `prediction` and `dates`
        return jsonify({
            'summary': f'Predicted prices for {company} over the next 30 days.',
            'graphData': [{
                'x': dates,    # Replace with actual date output from your model
                'y': prediction,  # Replace with actual prediction output from your model
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Predicted Price'
            }]
        })

    except Exception as e:
        return jsonify({'error': f'Failed to execute model: {str(e)}'}), 500


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already taken. Please choose a different one."

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Redirect to the login page after registration

    return render_template('register.html')



# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password"
    return render_template('login.html')

# Home route (accessible to everyone)
@app.route('/')
def home():
    return render_template('dashboard.html')  # Historical data is available to everyone

# Dashboard route (protected)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')  # Prediction data is accessible only to logged-in users


@app.route('/about')
def about():
    return render_template('about us.html')

@app.route('/help')
def help():
    return render_template('help.html')
    
@app.route('/watchlist')
def watchlist():
    return render_template('watchlist.html')



# Prediction route (protected)
@app.route('/index')
@login_required
def index():
    # Show prediction data here
    return render_template('index.html')  # This page is accessible only after login

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def open_browser():
    """Opens the default web browser to the home page."""
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new("http://127.0.0.1:5000/")  # Open the home page

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    Timer(1, open_browser).start()  # Delay browser opening to allow server to start
    app.run(debug=True)
