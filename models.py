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
    # A single skill (e.g. "Python"). Shared by seekers and postings via the tables above.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)

class Seeker(db.Model, UserMixin):
    # A job seeker account. UserMixin gives Flask-Login methods (is_authenticated, get_id, etc.).
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False)  # unique, no two seekers share an email
    name=db.Column(db.String(20),nullable=False)
    education=db.Column(db.String(20),nullable=False)
    major=db.Column(db.String(20),nullable=False)
    yoe=db.Column(db.Integer,nullable=False)                  # years of experience
    prefered_work_mode=db.Column(db.String(20),nullable=False)    # e.g. remote/ on-site/hybrid
    prefered_location=db.Column(db.String(20),nullable=False)
    hash=db.Column(db.String(20),nullable=False)
    type=db.Column(db.String(20),default='seeker')
    # this relationship targets the Skill model, backref seekers creates Skill.seekers for easy access.
    skills = db.relationship('Skill',secondary='seeker_skills',backref='seekers')
    membership=db.Column(db.Boolean,default=False)

class Employer(db.Model, UserMixin):
    # An employer account. Also uses UserMixin for Flask-Login.
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),unique=True,nullable=False) 
    hash=db.Column(db.String(20),nullable=False)
    type=db.Column(db.String(20),default='employer')
    membership=db.Column(db.Boolean, default=False)

class Posting(db.Model):
    # A job posting created by an employer.
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(20),nullable=False)
    company_name=db.Column(db.String(10),nullable=False)
    company_email=db.Column(db.String(20),nullable=False)
    description=db.Column(db.String(1000),nullable=False)
    job_type=db.Column(db.String(10),nullable=False)            # e.g. full-time/part-time
    education=db.Column(db.String(20),nullable=False)            # e.g. minimum required qualification
    yoe=db.Column(db.Integer,nullable=False)
    work_mode=db.Column(db.String(20),nullable=False)
    location=db.Column(db.String(20),nullable=False)
    # Foreign key tying each posting back to the Employer who made it.
    created_by=db.Column(db.Integer,db.ForeignKey('employer.id'),nullable=False)   
    # this relationship targets the Skill model. Backref not needed here.
    skills = db.relationship('Skill',secondary='posting_skills')
