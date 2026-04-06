from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# many to many relationship between job seekers and skills.
# many to many relationship tutorial: https://www.youtube.com/watch?v=47i-jzrrIGQ
# note: many to many relationships require an association table.
seeker_skills=db.Table('seeker_skills',
    db.Column('seeker_id',db.Integer,db.ForeignKey('seeker.id')),
    db.Column('skill_id',db.Integer,db.ForeignKey('skill.id'))
)

# association table for many to many relationship between job postings and skills.
posting_skills=db.Table('posting_skills',
    db.Column('posting_id',db.Integer,db.ForeignKey('posting.id')),
    db.Column('skill_id',db.Integer,db.ForeignKey('skill.id'))
)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)

class Seeker(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False)
    name=db.Column(db.String(20),nullable=False)
    education=db.Column(db.String(20),nullable=False)
    major=db.Column(db.String(20),nullable=False)
    yoe=db.Column(db.Integer,nullable=False)
    prefered_work_mode=db.Column(db.String(20),nullable=False)
    prefered_location=db.Column(db.String(20),nullable=False)
    hash=db.Column(db.String(20),nullable=False)
    type=db.Column(db.String(20),default='seeker')
    # this relationship targets the Skill model, backref seekers creates Skill.seekers for easy access.
    skills = db.relationship('Skill',secondary='seeker_skills',backref='seekers')

class Employer(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False)
    hash=db.Column(db.String(20),nullable=False)
    type=db.Column(db.String(20),default='employer')

class Posting(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(20),nullable=False)
    company_name=db.Column(db.String(10),nullable=False)
    company_email=db.Column(db.String(20),nullable=False)
    description=db.Column(db.String(1000),nullable=False)
    education=db.Column(db.String(20),nullable=False)
    yoe=db.Column(db.Integer,nullable=False)
    work_mode=db.Column(db.String(20),nullable=False)
    location=db.Column(db.String(20),nullable=False)
    created_by=db.Column(db.Integer,db.ForeignKey('employer.id'),nullable=False)
    # this relationship targets the Skill model. Backref not needed here.
    skills = db.relationship('Skill',secondary='posting_skills')