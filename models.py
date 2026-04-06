from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class JobSeeker(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False)
    name=db.Column(db.String(20),nullable=False)
    education=db.Column(db.String(20),nullable=False)
    major=db.Column(db.String(20),nullable=False)
    yoe=db.Column(db.Integer,nullable=False)
    skills=db.Column(db.String(100),nullable=False)
    prefered_work_mode=db.Column(db.String(20),nullable=False)
    prefered_location=db.Column(db.String(20),nullable=False)
    hash=db.Column(db.String(20),nullable=False)
    type=db.Column(db.String(20),default='seeker')

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)

class Employer(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False)
    hash=db.Column(db.String(20),nullable=False)
    type=db.Column(db.String(20),default='employer')

class JobPosting(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(20),nullable=False)
    company_name=db.Column(db.String(10),nullable=False)
    company_email=db.Column(db.String(20),nullable=False)
    description=db.Column(db.String(1000),nullable=False)
    education=db.Column(db.String(20),nullable=False)
    skills=db.Column(db.String(100),nullable=False)
    yoe=db.Column(db.Integer,nullable=False)
    work_mode=db.Column(db.String(20),nullable=False)
    location=db.Column(db.String(20),nullable=False)
    created_by=db.Column(db.Integer,db.ForeignKey('employer.id'),nullable=False)