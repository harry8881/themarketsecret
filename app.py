from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import ast
import requests
import hmac
import hashlib
from dotenv import load_dotenv
import os
from cachetools import TTLCache

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'd880f4262fb92ff5e5e893b5198c9872'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {"timeout": 30, "check_same_thread": False}
}

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Cache for news (TTL = 1 hour)
news_cache = TTLCache(maxsize=1, ttl=3600)

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # 🔥 Added this line

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    package = db.Column(db.String(20), nullable=True)
    progress = db.Column(db.String(200), default='[]')
    name = db.Column(db.String(80), nullable=True)  # Added for profile
    phone = db.Column(db.String(15), nullable=True)  # Added for profile

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    email = StringField('Email', render_kw={"placeholder": "@gmail.com"}, validators=[DataRequired(), Email(message="Invalid email address")])
    password = PasswordField('Password', render_kw={"placeholder": "Enter a secure password"}, validators=[DataRequired()])
    submit = SubmitField('Signup')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def landing():
    print("Loading landing page")
    try:
        return render_template('landing.html', user=current_user)
    except Exception as e:
        print(f"Error loading landing.html: {str(e)}")
        abort(500)

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("Loading login page")
    if current_user.is_authenticated:
        print("User already authenticated, redirecting to dashboard")
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        print(f"Attempting login for username: {username}")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            print(f"Login successful for username: {username}")
            return redirect(url_for('dashboard'))
        else:
            print(f"Login failed for username: {username}")
            flash('Invalid username or password')
    try:
        return render_template('login.html', form=form)
    except Exception as e:
        print(f"Error loading login.html: {str(e)}")
        abort(500)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("Loading signup page")
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        print(f"User entered email: {email}")
        existing_user = User.query.filter_by(username=email).first()
        if existing_user:
            print(f"Email {email} already exists")
            flash('Email already exists. Please log in or use a different email.')
            return redirect(url_for('signup'))
        hashed_password = generate_password_hash(password)
        print(f"Hashed password for {email}: {hashed_password}")
        new_user = User(username=email, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print(f"User {email} signed up successfully")
        return redirect(url_for('login'))
    try:
        return render_template('signup.html', form=form)
    except Exception as e:
        print(f"Error loading signup.html: {str(e)}")
        abort(500)

@app.route('/dashboard')
@login_required
def dashboard():
    print(f"Loading dashboard for user: {current_user.username}")
    try:
        return render_template('dashboard.html', user=current_user)
    except Exception as e:
        print(f"Error loading dashboard.html: {str(e)}")
        abort(500)

@app.route('/video')
@login_required
def video():
    print("Redirecting from /video to /course")
    return redirect(url_for('course')) 

@app.route('/course')
@login_required
def course():
    print(f"Loading course page for: {current_user.email}")
    try:
        video_urls = {
            'smc': 'https://vimeo.com/smc_video',
            'wave_smc': 'https://vimeo.com/wave_smc_video'
        }
        video_url = video_urls.get(current_user.package) if current_user.paid else None
        progress_list = ast.literal_eval(current_user.progress) if current_user.progress else []
        return render_template('course.html', video_url=video_url, progress=progress_list, user=current_user, is_paid=current_user.paid)
    except Exception as e:
        print(f"Error loading course.html: {str(e)}")
        flash('Something went wrong loading the course.')
        return redirect(url_for('dashboard'))

@app.route('/contact')
def contact():
    print("Loading contact page")
    try:
        return render_template('contact.html', user=current_user)
    except Exception as e:
        print(f"Error loading contact.html: {str(e)}")
        abort(500)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    print(f"Loading profile page for: {current_user.username}")
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        if not phone or not phone.isdigit() or len(phone) < 10 or len(phone) > 15:
            flash('Please enter a valid phone number (10-15 digits)', 'error')
            return redirect(url_for('profile'))
        current_user.name = name
        current_user.phone = phone
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating your profile.', 'error')
        return redirect(url_for('profile'))
    try:
        return render_template('profile.html', user=current_user)
    except Exception as e:
        print(f"Error loading profile.html: {str(e)}")
        abort(500)

@app.route('/settings')
@login_required
def settings():
    print(f"Loading settings page for: {current_user.username}")
    try:
        return render_template('settings.html', user=current_user)
    except Exception as e:
        print(f"Error loading settings.html: {str(e)}")
        abort(500)

@app.route('/mentorship')
@login_required
def mentorship():
    print("Loading mentorship page") 
    try:
        if 'forex_news' in news_cache:
            articles = news_cache['forex_news']
            print("Serving news from cache")
        else:
            api_key = os.getenv('NEWSAPI_KEY')
            if not api_key:
                print("NewsAPI key not found")
                flash('Unable to load forex news at this time.')
                articles = []
            else:
                url = f"https://newsapi.org/v2/everything?q=forex+currency+market&apiKey={api_key}&language=en&sortBy=publishedAt"
                response = requests.get(url)
                if response.status_code == 200:
                    articles = response.json().get('articles', [])[:10]
                    news_cache['forex_news'] = articles
                    print("Fetched news from NewsAPI")
                else:
                    print(f"NewsAPI error: {response.text}")
                    flash('Unable to load forex news at this time.')
                    articles = []
        return render_template('mentorship.html', user=current_user, articles=articles)
    except Exception as e:
        print(f"Error loading mentorship.html: {str(e)}")
        flash('An error occurred while loading the news.')
        return render_template('mentorship.html', user=current_user, articles=[])

@app.route('/pay', methods=['GET', 'POST'])
@login_required
def pay():
    print("Loading pay page")
    package = request.args.get('package', 'smc')
    default_amount = {'smc': 119.0, 'wave_smc': 250.0}.get(package, 119.0)
    if request.method == 'POST':
        amount = float(request.form.get('amount', default_amount))
        package = request.form.get('package', package)
        if amount not in [119.0, 250.0] or package not in ['smc', 'wave_smc']:
            flash('Invalid package or amount. Choose SMC ($119) or Wave SMC ($250).')
            return redirect(url_for('dashboard'))
        api_key = os.getenv('NOWPAYMENTS_API_KEY')
        if not api_key:
            print("API Key not found")
            flash('Internal server error. Please try again.')
            return redirect(url_for('dashboard'))
        url = "https://api.nowpayments.io/v1/payment"
        headers = {"x-api-key": api_key}
        data = {
            "price_amount": amount,
            "price_currency": "usd",
            "pay_currency": "usdt_trc20",
            "ipn_callback_url": "https://yourdomain.com/ipn",
            "order_id": current_user.id,
            "order_description": f"Payment for {package} package by {current_user.email}"
        }
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            payment_url = response.json().get('payment_url')
            if payment_url:
                print(f"Redirecting to payment URL: {payment_url}")
                return redirect(payment_url)
            else:
                flash('Failed to initiate payment. Try again later.')
        except Exception as e:
            print(f"Payment API error: {str(e)}")
            flash('Payment service unavailable. Please try again later.')
    try:
        return render_template('pay.html', package=package, amount=default_amount, user=current_user)
    except Exception as e:
        print(f"Error loading pay.html: {str(e)}")
        abort(500)

@app.route('/logout')
@login_required
def logout():
    print(f"User {current_user.username} logging out")
    logout_user()
    return redirect(url_for('landing'))

with app.app_context():
    db.create_all()
    print("Database tables created!")

if __name__ == '__main__':
    print("Starting Flask app on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
