from flask import Flask, render_template, redirect, url_for, abort, request, flash
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
from cachetools import TTLCache  # Added for news caching

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'd880f4262fb92ff5e5e893b5198c9872'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Cache for news (TTL = 1 hour to avoid excessive API calls)
news_cache = TTLCache(maxsize=1, ttl=3600)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    package = db.Column(db.String(20), nullable=True)  # Store 'smc' or 'wave_smc'
    progress = db.Column(db.String(200), default='[]')

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

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route("/")
def home():
    print("Loading home page")
    try:
        return render_template('landing.html', user=current_user)
    except Exception as e:
        print(f"Error loading landing.html: {str(e)}")
        abort(500)

@app.route("/login", methods=['GET', 'POST'])
def login():
    print("Loading login page")
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

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    print("Loading signup page")
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        print(f"User entered email: {email}")
        print(f"User entered password: {password}")
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
        print(f"User {email} signed up successfully and saved to database.")
        return redirect(url_for('login'))
    try:
        return render_template('signup.html', form=form)
    except Exception as e:
        print(f"Error loading signup.html: {str(e)}")
        abort(500)

@app.route("/course")
@login_required
def course():
    print("Loading course page for:", current_user.email)
    try:
        video_urls = {
            'smc': 'https://vimeo.com/smc_video',  # Replace with actual SMC video URL
            'wave_smc': 'https://vimeo.com/wave_smc_video'  # Replace with actual Wave SMC video URL
        }
        video_url = video_urls.get(current_user.package) if current_user.paid else None
        progress_list = ast.literal_eval(current_user.progress) if current_user.progress else []
        return render_template('course.html', video_url=video_url, progress=progress_list, user=current_user, is_paid=current_user.paid, package=current_user.package)
    except Exception as e:
        print(f"[ERROR] Could not load course page: {e}")
        flash('Something went wrong loading the course.')
        return redirect(url_for('dashboard'))

@app.route("/mentorship")
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

@app.route("/pay", methods=['GET', 'POST'])
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
            "ipn_callback_url": "https://67bce4921bd7.ngrok-free.app/ipn",
            "order_id": f"{current_user.id}:{package}",  # Include package in order_id
            "order_description": f"{package.capitalize()} Membership for {current_user.username}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            payment_data = response.json()
            print(f"Payment created: {payment_data}")
            return render_template('pay.html', payment_url=payment_data.get('invoice_url'))
        else:
            flash('Error creating payment. Please try again.')
            print(f"Payment error: {response.text}")
            return redirect(url_for('dashboard'))
    return render_template('pay_select.html', user=current_user, default_amount=default_amount, package=package)

@app.route("/ipn", methods=['POST'])
def ipn():
    print("Received IPN callback")
    ipn_secret = os.getenv('NOWPAYMENTS_IPN_SECRET')
    signature = request.headers.get('x-nowpayments-sig')
    data = request.get_json()
    if not ipn_secret or not signature:
        print("Invalid IPN request: missing secret or signature")
        return "", 400
    computed_signature = hmac.new(ipn_secret.encode(), request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_signature, signature):
        print("IPN signature mismatch")
        return "", 400
    payment_status = data.get('payment_status')
    order_id = data.get('order_id')
    if payment_status == 'finished' and order_id:
        user_id, package = order_id.split(':')
        user = User.query.get(int(user_id))
        if user and not user.paid:
            user.paid = True
            user.package = package  # Save package type
            db.session.commit()
            print(f"User {user.username} marked as paid with package {package}")
    return "", 200

@app.route("/update_progress", methods=['POST'])
@login_required
def update_progress():
    lesson = request.form.get('lesson')
    if lesson:
        try:
            progress = ast.literal_eval(current_user.progress) if current_user.progress else []
        except Exception:
            progress = []
        if lesson not in progress:
            progress.append(lesson)
            current_user.progress = str(progress)
            db.session.commit()
    return redirect(url_for('course'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route("/discord")
@login_required
def discord():
    return redirect("https://discord.gg/vXmcKXkRYP")

@app.route('/video')
@login_required
def video():
    print("Redirecting from /video to /course")
    return redirect(url_for('course'))  # Redirect to /course

@app.route('/competition')
@login_required
def competition():
    print("Loading competition page")
    try:
        return render_template('competition.html', user=current_user)
    except Exception as e:
        print(f"Error loading competition.html: {str(e)}")
        abort(404)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        # Validate phone number (server-side)
        if not phone or not phone.isdigit() or len(phone) < 10 or len(phone) > 15:
            flash('Please enter a valid phone number (10-15 digits)', 'error')
            return redirect(url_for('profile'))
        
        # Update user data
        current_user.name = name
        current_user.phone = phone
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
        
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/settings')
@login_required
def settings():
    print("Loading settings page")
    try:
        return render_template('settings.html', user=current_user)
    except Exception as e:
        print(f"Error loading settings.html: {str(e)}")
        abort(404)

with app.app_context():
    print("Creating database tables...")
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
