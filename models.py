from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class JobSeeker(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False)
    name=db.Column(db.String(20),nullable=False)
    hash=db.Column(db.String(20),nullable=False)

class Employer(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False)
    hash=db.Column(db.String(20),nullable=False)

class JobPosting(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(20),nullable=False)
    yoe=db.Column(db.Integer,nullable=False)
    created_by=db.Column(db.Integer,db.ForeignKey('employer.id'),nullable=False)