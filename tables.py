from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True) 
    password = db.Column(db.String(80), nullable=False)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    urlToImage = db.Column(db.String(255))
    source_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    published_at = db.Column(db.String(50))
    # New field to distinguish between 'sports', 'technology', etc.
    category = db.Column(db.String(50), default='general') 
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)