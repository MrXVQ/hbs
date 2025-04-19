import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traveler_registration_secret_key")

# Set up PostgreSQL database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with SQLAlchemy
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import models after db initialization
with app.app_context():
    from models import Traveler, BookingSite, User
    db.create_all()
    
    # Create default booking sites if they don't exist
    default_sites = ["Booking.com", "Airbnb", "Expedia", "TripAdvisor", "Direct booking", "Other"]
    
    for site_name in default_sites:
        existing_site = BookingSite.query.filter_by(name=site_name).first()
        if not existing_site:
            new_site = BookingSite(name=site_name)
            db.session.add(new_site)
    
    # Create a default admin user if none exists
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@example.com')
        admin_user.set_password('password123')  # Default password, should be changed
        db.session.add(admin_user)
    
    db.session.commit()

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required  # Only existing users can create new users
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register_user'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register_user'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered', 'danger')
            return redirect(url_for('register_user'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('User registered successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register_user.html')

# Application routes
@app.route('/')
@login_required
def index():
    booking_sites = BookingSite.query.all()
    return render_template('index.html', booking_sites=booking_sites)

@app.route('/add_traveler', methods=['POST'])
@login_required
def add_traveler():
    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        telephone = request.form['telephone']
        email = request.form['email']
        house_number = request.form['house_number']
        
        # Create new traveler
        new_traveler = Traveler(
            first_name=first_name,
            last_name=last_name,
            telephone=telephone,
            email=email,
            house_number=house_number,
            registration_date=datetime.now()
        )
        
        db.session.add(new_traveler)
        db.session.flush()  # This assigns an ID to new_traveler
        
        # Process booking sites
        booking_sites = request.form.getlist('booking_sites')
        for site_id in booking_sites:
            site = BookingSite.query.get(site_id)
            if site:
                new_traveler.booking_sites.append(site)
        
        db.session.commit()
        flash('Traveler registered successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error registering traveler: {str(e)}', 'danger')
        logging.error(f"Error adding traveler: {str(e)}")
    
    return redirect(url_for('index'))

@app.route('/view_data')
@login_required
def view_data():
    booking_sites = BookingSite.query.all()
    return render_template('view_data.html', booking_sites=booking_sites)

@app.route('/get_travelers')
@login_required
def get_travelers():
    travelers = Traveler.query.all()
    result = []
    
    for traveler in travelers:
        # Get booking sites as a list of names
        booking_sites = [site.name for site in traveler.booking_sites]
        
        result.append({
            'id': traveler.id,
            'first_name': traveler.first_name,
            'last_name': traveler.last_name,
            'telephone': traveler.telephone,
            'email': traveler.email,
            'house_number': traveler.house_number,
            'booking_sites': ", ".join(booking_sites),
            'registration_date': traveler.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
            'departure_date': traveler.departure_date.strftime('%Y-%m-%d %H:%M:%S') if traveler.departure_date else '',
            'status': 'Departed' if not traveler.is_active else 'Active'
        })
    
    return jsonify(result)
    
    
@app.route('/mark_departed/<int:traveler_id>', methods=['POST'])
@login_required
def mark_departed(traveler_id):
    traveler = Traveler.query.get_or_404(traveler_id)
    
    # Get departure date from form or use current date if not provided
    departure_date_str = request.form.get('departure_date')
    if departure_date_str:
        try:
            departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d')
        except ValueError:
            departure_date = datetime.now()
    else:
        departure_date = datetime.now()
    
    traveler.departure_date = departure_date
    traveler.is_active = False
    
    db.session.commit()
    flash(f'Traveler {traveler.first_name} {traveler.last_name} marked as departed.', 'success')
    return redirect(url_for('view_data'))    


@app.route('/export_csv')
@login_required
def export_csv():
    import csv
    import tempfile
    
    travelers = Traveler.query.all()
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    
    with open(temp_file.name, 'w', newline='') as csvfile:
        fieldnames = ['ID', 'First Name', 'Last Name', 'Telephone', 'Email', 
                     'House Number', 'Booking Sites', 'Registration Date', 'Departure Date', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for traveler in travelers:
            booking_sites = ", ".join([site.name for site in traveler.booking_sites])
            writer.writerow({
                'ID': traveler.id,
                'First Name': traveler.first_name,
                'Last Name': traveler.last_name,
                'Telephone': traveler.telephone,
                'Email': traveler.email,
                'House Number': traveler.house_number,
                'Booking Sites': booking_sites,
                'Registration Date': traveler.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Departure Date': traveler.departure_date.strftime('%Y-%m-%d %H:%M:%S') if traveler.departure_date else '',
                'Status': 'Departed' if not traveler.is_active else 'Active'
            })
    
    return send_file(temp_file.name, 
                     mimetype='text/csv',
                     download_name='travelers_data.csv',
                     as_attachment=True)
                     
                     
@app.route('/backup_database')
@login_required
def backup_database():
    from db_backup import create_backup
    try:
        backup_file = create_backup()
        flash(f'Database backed up successfully to {backup_file}', 'success')
    except Exception as e:
        flash(f'Error backing up database: {str(e)}', 'danger')
    
    return redirect(url_for('view_data'))

@app.route('/restore_database', methods=['POST'])
@login_required
def restore_database():
    from db_backup import restore_from_backup
    try:
        backup_file = request.form.get('backup_file')
        if backup_file:
            restore_from_backup(backup_file)
            flash('Database restored successfully!', 'success')
        else:
            flash('No backup file specified', 'danger')
    except Exception as e:
        flash(f'Error restoring database: {str(e)}', 'danger')
    
    return redirect(url_for('view_data'))