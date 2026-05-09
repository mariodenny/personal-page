from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hero_title = db.Column(db.String(255), nullable=False)
    hero_description = db.Column(db.Text, nullable=False)
    about_description = db.Column(db.Text, nullable=False)
    contact_text = db.Column(db.Text, nullable=False)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon_class = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    slug = db.Column(db.String(255), nullable=False, unique=True)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False) # 'project' or 'blog'
    entity_id = db.Column(db.Integer, nullable=False)
