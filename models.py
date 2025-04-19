from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash




# Association table for many-to-many relationship between travelers and booking sites
traveler_booking_sites = db.Table('traveler_booking_sites',
    db.Column('traveler_id', db.Integer, db.ForeignKey('traveler.id'), primary_key=True),
    db.Column('booking_site_id', db.Integer, db.ForeignKey('booking_site.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Traveler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    house_number = db.Column(db.Integer, nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.now)
    departure_date = db.Column(db.DateTime, nullable=True)  # Added this field
    is_active = db.Column(db.Boolean, default=True)  # Added to track if traveler has departed
    
    # Many-to-many relationship with booking sites
    booking_sites = db.relationship('BookingSite', secondary=traveler_booking_sites,
                                   backref=db.backref('travelers', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Traveler {self.first_name} {self.last_name}>'

class BookingSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<BookingSite {self.name}>'