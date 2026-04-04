from flask import Flask, render_template,request,redirect, flash,session
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

@login_manager.user_loader
def load_user(id):
    if 'type' in session:
        if session['type'] == 'seeker':
            return JobSeeker.query.get(int(id))
        elif session['type'] == 'employer':
            return Employer.query.get(int(id))
    else:
        return None

# home page
@app.route("/")
def index():
    return render_template("index.html")

# create job seeker account
@app.route("/signup-seeker",methods=['GET','POST'])
def signup_seeker():
    if current_user.is_authenticated:
        return redirect('/job-board/')
    if request.method=='POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        education = request.form['education']
        major = request.form['major']
        yoe = request.form['yoe']
        skills = request.form.getlist('skills')
        if len(skills) > 5:
            flash('Please select a maximum of 5 skills')
            return redirect('/signup-seeker')
        skills_string = ""
        for skill in skills:
            skills_string += skill + ","    
        skills_string = skills_string[:-1] # remove last comma
        prefered_work_mode = request.form['prefered_work_mode']
        prefered_location = request.form['prefered_location']

        hash = bcrypt.generate_password_hash(password).decode('utf-8')
        if JobSeeker.query.filter_by(email=email).first():
            flash('Email already exists, please login instead')
            return redirect('/signup-seeker')

        new_job_seeker = JobSeeker(email=email,name=name,hash=hash,education=education,major=major,yoe=yoe,skills=skills_string,prefered_work_mode=prefered_work_mode,prefered_location=prefered_location)
        try:
            db.session.add(new_job_seeker)
            db.session.commit()
            flash('Successfully created account')
            login_user(new_job_seeker)
            return redirect('/job-board')
        except Exception as e:
            print(f"Error occured: {e}")
    elif request.method=='GET':
        return render_template("signup-seeker.html")

# create employer account
@app.route("/signup-employer",methods=['GET','POST'])
def signup_employer():
    if current_user.is_authenticated:
        return redirect('/create-job/')
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        hash = bcrypt.generate_password_hash(password).decode('utf-8')
        if Employer.query.filter_by(email=email).first():
            flash('Email already exists, please login instead')
            return redirect('/signup-employer')

        new_employer = Employer(email=email,hash=hash)
        try:
            db.session.add(new_employer)
            db.session.commit()
            flash("Successfully created account")
            login_user(new_employer)
            return redirect('/create-job')
        except Exception as e:
            print(f"Error occured: {e}")
    elif request.method=='GET':
        return render_template("signup-employer.html")

@app.route('/login-seeker',methods=['GET','POST'])
def login_seeker():
    if current_user.is_authenticated:
        flash('You are already logged in')
        return redirect('/job-board/')
    else:
        if request.method=='GET':
            return render_template('login-seeker.html')
        elif request.method=='POST':
            email = request.form['email']
            password = request.form['password']
            # authenticate user here
            job_seeker = JobSeeker.query.filter_by(email=email).first()
            if job_seeker and bcrypt.check_password_hash(job_seeker.hash, password):
                login_user(job_seeker)
                flash('Login successful')
                session['type'] = 'seeker'
                return redirect('/job-board/')
            else:
                flash('Invalid email or password')
                return redirect('/login-seeker')

@app.route('/login-employer',methods=['GET','POST'])
def login_employer():
    if current_user.is_authenticated:
        flash('You are already logged in')
        return redirect('/create-job/')
    else:
        if request.method=='GET':
            return render_template('login-employer.html')
        elif request.method=='POST':
            email = request.form['email']
            password = request.form['password']
            # authenticate user here
            employer = Employer.query.filter_by(email=email).first()
            if employer and bcrypt.check_password_hash(employer.hash, password):
                login_user(employer)
                flash('Login successful')
                session['type'] = 'employer'
                return redirect('/create-job/')
            else:
                flash('Invalid email or password')
                return redirect('/login-employer')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route("/create-job/",methods=['GET','POST'])
@login_required
def create_job():
    if current_user.type != 'employer':
        flash('Only employers can create job postings')
        return redirect('/')
    if request.method=='GET':
        jobs = JobPosting.query.filter_by(created_by=current_user.id).all()
        return render_template("create-job.html", jobs=jobs)
    elif request.method=='POST':
        title = request.form['title']
        company_name = request.form['company_name']
        company_email = request.form['company_email']
        description = request.form['description']
        education = request.form['education']

        skills = request.form.getlist('skills')
        if len(skills) > 5:
            flash('Please select a maximum of 5 skills')
            return redirect('/create-job/')
        skills_string = ""
        for skill in skills:
            skills_string += skill + ","
        skills_string = skills_string[:-1] # remove last comma
 
        yoe = request.form['yoe']
        work_mode = request.form['work_mode']
        location = request.form['location']
        new_job_posting = JobPosting(title=title, company_name=company_name, company_email=company_email, education=education,skills=skills_string,description=description, yoe=yoe, work_mode=work_mode, location=location, created_by=current_user.id)
        try:
            db.session.add(new_job_posting)
            db.session.commit()
            flash('Job created successfully')
            return redirect('/create-job/')
        except Exception as e:
            print(f"Error occured: {e}")
            flash('An error occurred while creating the job')
            return redirect('/create-job/')

# job board
@app.route("/job-board/")
@login_required
def job_board():
    if current_user.type != 'seeker':
        flash('Only job seekers can view the job board')
        return redirect('/')

    # REQUIREMENT 1: ALL JOBS WITH KEYWORD SEARCH (JOB DESC) 
    desc_search = request.args.get('desc_search')
    if desc_search:
        all_jobs = JobPosting.query.filter(JobPosting.description.contains(desc_search)).all()
    else:
        all_jobs = JobPosting.query.all()

    # REQUIREMENT 2: BEST MATCHING JOBS
    # get top 10 best matching jobs for seeker and pass to template
    best_jobs = []

    # education level of seeker needs to be equal or higher than job posting
    education = current_user.education
    if education == 'high school':
        education_levels = ['high school']
    elif education == "bachelors degree":
        education_levels = ['high school','bachelors degree']
    elif education == "masters degree":
        education_levels = ['high school','bachelors degree','masters degree']
    elif education == "phd":
        education_levels = ['high school','bachelors degree','masters degree','phd']
    else:
        flash('Invalid education level')
        return redirect('/')

    # match seeker skills with job posting skills (top 10)
    current_user_skills = current_user.skills.split(",")
    
    best_jobs = JobPosting.query.filter(
        JobPosting.location == current_user.prefered_location,
        JobPosting.work_mode == current_user.prefered_work_mode,
        JobPosting.education.in_(education_levels),
        JobPosting.yoe <= current_user.yoe
    ).all()

    return render_template("job-board.html",all_jobs=all_jobs, best_jobs=best_jobs)

# individual job details page
@app.route("/job-details/<int:job_id>/")
def job_details(job_id):
    job = JobPosting.query.get_or_404(job_id)
    return render_template("job-details.html", job=job)



if __name__=="__main__":
    with app.app_context():   
        db.create_all()
    app.run(debug=True)