from flask import Flask, render_template,request,redirect, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# models
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
from models import db, JobSeeker,Employer,JobPosting
db.init_app(app)

from flask_login import LoginManager, login_required, logout_user, current_user, login_user
login_manager = LoginManager()
login_manager.init_app(app)

from flask_bcrypt import Bcrypt # for hashing password
bcrypt = Bcrypt(app)

import os
# environment variable for session key. Also a default key for local users.
app.secret_key = os.environ.get("SECRET_KEY",'mjrajrjk294999$(@(@(.)))')

# create job seeker account
@app.route("/",methods=['GET','POST'])
def index():
    if request.method=='POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        hash = bcrypt.generate_password_hash(password).decode('utf-8')
        if JobSeeker.query.filter_by(email=email).first():
            flash('Email already exists, please login instead')
            return redirect('/')

        new_job_seeker = JobSeeker(email=email,name=name,hash=hash)
        try:
            db.session.add(new_job_seeker)
            db.session.commit()
            # auto login after account creation
            login_user(new_job_seeker)
            return redirect('/')
        except Exception as e:
            print(f"Error occured: {e}")
    elif request.method=='GET':
        job_seekers = JobSeeker.query.all()
        return render_template("index.html",job_seekers=job_seekers)

@app.route('/delete/<int:id>')
def delete(id:int):
    job_seeker = JobSeeker.query.get_or_404(id)
    db.session.delete(job_seeker)
    db.session.commit()
    return redirect('/')

@app.route('/edit/<int:id>',methods=['GET','POST'])
def edit(id:int):
    job_seeker = JobSeeker.query.get_or_404(id)
    if request.method=='POST':
        job_seeker.email=request.form['email']
        job_seeker.name=request.form['name']
        db.session.commit()
        return redirect('/')
    else:
        return render_template('edit.html',job_seeker=job_seeker)

@login_manager.user_loader
def load_user(id):
    return JobSeeker.query.get(id)

@app.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in')
        return redirect('/')
    else:
        if request.method=='GET':
            return render_template('login-job-seeker.html')
        elif request.method=='POST':
            email = request.form['email']
            password = request.form['password']
            # authenticate user here
            job_seeker = JobSeeker.query.filter_by(email=email).first()
            if job_seeker and bcrypt.check_password_hash(job_seeker.hash, password):
                login_user(job_seeker)
                flash('Login successful')
                return redirect('/')
            else:
                flash('Invalid email or password')
                return redirect('/login')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route("/create-job/",methods=['GET','POST'])
@login_required
def create_job():
    if request.method=='GET':
        jobs = JobPosting.query.filter_by(created_by=current_user.id).all()
        return render_template('create-job.html',jobs=jobs)
    elif request.method=='POST':
        title = request.form['title']
        yoe = request.form['yoe']
        new_job_posting = JobPosting(title=title,yoe=yoe,created_by=current_user.id)
        try:
            db.session.add(new_job_posting)
            db.session.commit()
            flash('Job created successfully')
            return redirect('/create-job/')
        except Exception as e:
            print(f"Error occured: {e}")
            flash('An error occurred while creating the job')
            return redirect('/create-job/')

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)