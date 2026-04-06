from flask import Flask, render_template,request,redirect, flash,session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# models
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
from models import db, Seeker,Employer,Posting, Skill
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
            return Seeker.query.filter_by(id=int(id)).first()
        elif session['type'] == 'employer':
            return Employer.query.filter_by(id=int(id)).first()
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
        hash = bcrypt.generate_password_hash(password).decode('utf-8')
        if Seeker.query.filter_by(email=email).first():
            flash('Email already exists, please login instead')
            return redirect('/signup-seeker')
        
        prefered_work_mode = request.form['prefered_work_mode']
        prefered_location = request.form['prefered_location']

        skills = request.form.getlist('skills')
        if len(skills) > 5:
            flash('Please select a maximum of 5 skills')
            return redirect('/signup-seeker')

        new_seeker = Seeker(email=email,name=name,hash=hash,education=education,major=major,yoe=yoe,prefered_work_mode=prefered_work_mode,prefered_location=prefered_location)
        
        # append skills into new job seeker
        for skill_name in skills:
            skill = Skill.query.filter_by(name=skill_name).first()
            new_seeker.skills.append(skill)

        try:
            db.session.add(new_seeker)
            db.session.commit()
            flash('Successfully created account')
            return redirect('/login-seeker')
        except Exception as e:
            print(f"Error occured: {e}")
    elif request.method=='GET':
        skills = Skill.query.all()
        return render_template("signup-seeker.html",skills=skills)

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
            job_seeker = Seeker.query.filter_by(email=email).first()
            if job_seeker and bcrypt.check_password_hash(job_seeker.hash, password):
                login_user(job_seeker)
                flash('Login successful')
                session['type'] = 'seeker'
                return redirect('/job-board/')
            else:
                flash('Invalid email or password')
                return redirect('/login-seeker')

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
        all_postings = Posting.query.filter(Posting.description.contains(desc_search)).all()
    else:
        all_postings = Posting.query.all()

    # REQUIREMENT 2: BEST MATCHING JOBS

    # education level of seeker needs to be equal or higher than job posting
    education = current_user.education
    if education == 'high school':
        education_level = ['high school']
    elif education == "bachelors degree":
        education_level = ['high school','bachelors degree']
    elif education == "masters degree":
        education_level = ['high school','bachelors degree','masters degree']
    elif education == "phd":
        education_level = ['high school','bachelors degree','masters degree','phd']
    else:
        flash('Invalid education level')
        return redirect('/')
    
    '''
    education 20
    yoe 20
    skills 5 skills x 5 points each = 25
    prefered_work_mode= 15
    prefered_location= 20
    Total = 100
    '''

    # calculate match score for jobs
    best_postings = Posting.query.all()
    for posting in best_postings:
        posting.match_score = 0
        if posting.education in education_level:
            posting.match_score += 20
        if posting.yoe <= current_user.yoe:
            posting.match_score += 20
        if posting.work_mode == current_user.prefered_work_mode:
            posting.match_score += 15
        if posting.location == current_user.prefered_location:
            posting.match_score += 20

        # each skill match adds 5 points
        for skill in current_user.skills:
            if skill in posting.skills:
                posting.match_score += 5
    
    # show top 10 jobs with highest match_score
    from operator import attrgetter
    best_postings = sorted(best_postings, key=attrgetter("match_score"), reverse=True)[:10]
    
    return render_template("job-board.html",all_postings=all_postings, best_postings=best_postings)

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
            return redirect('/login-employer')
        except Exception as e:
            print(f"Error occured: {e}")
    elif request.method=='GET':
        return render_template("signup-employer.html")

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

@app.route("/create-job/",methods=['GET','POST'])
@login_required
def create_job():
    if current_user.type != 'employer':
        flash('Only employers can create job postings')
        return redirect('/')
    if request.method=='GET':
        jobs = Posting.query.filter_by(created_by=current_user.id).all()
        skills = Skill.query.all()
        return render_template("create-job.html", jobs=jobs,skills=skills)
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
        
        yoe = request.form['yoe']
        work_mode = request.form['work_mode']
        location = request.form['location']
        new_posting = Posting(title=title, company_name=company_name, company_email=company_email, education=education,description=description, yoe=yoe, work_mode=work_mode, location=location, created_by=current_user.id)
        
        # append skills into new job seeker
        for skill_name in skills:
            skill = Skill.query.filter_by(name=skill_name).first()
            new_posting.skills.append(skill)
        
        try:
            db.session.add(new_posting)
            db.session.commit()
            flash('Job created successfully')
            return redirect('/create-job/')
        except Exception as e:
            print(f"Error occured: {e}")
            flash('An error occurred while creating the job')
            return redirect('/create-job/')

# individual job details page
@app.route("/job-details/<int:posting_id>/")
def job_details(posting_id):
    posting = Posting.query.get_or_404(posting_id)
    return render_template("job-details.html", posting=posting)

    # REQUIREMENT 2: BEST MATCHING JOBS

    # education level of seeker needs to be equal or higher than job posting
    education = current_user.education
    if education == 'high school':
        education_level = ['high school']
    elif education == "bachelors degree":
        education_level = ['high school','bachelors degree']
    elif education == "masters degree":
        education_level = ['high school','bachelors degree','masters degree']
    elif education == "phd":
        education_level = ['high school','bachelors degree','masters degree','phd']
    else:
        flash('Invalid education level')
        return redirect('/')
    
    '''
    education 20
    yoe 20
    skills 5 skills x 5 points each = 25
    prefered_work_mode= 15
    prefered_location= 20
    Total = 100
    '''

    # calculate match score for jobs
    best_postings = Posting.query.all()
    for posting in best_postings:
        posting.match_score = 0
        if posting.education in education_level:
            posting.match_score += 20
        if posting.yoe <= current_user.yoe:
            posting.match_score += 20
        if posting.work_mode == current_user.prefered_work_mode:
            posting.match_score += 15
        if posting.location == current_user.prefered_location:
            posting.match_score += 20

        # each skill match adds 5 points
        for skill in current_user.skills:
            if skill in posting.skills:
                posting.match_score += 5
    
    # show top 10 jobs with highest match_score
    from operator import attrgetter
    best_postings = sorted(best_postings, key=attrgetter("match_score"), reverse=True)[:10]
    
    return render_template("job-board.html",all_postings=all_postings, best_postings=best_postings)

# talent board
@app.route("/talent-board")
@login_required
def talent_board():
    # show all job seekers by default, if any filters are used, apply them
    # get value from url parameters (args)
    keyword = request.args.get('keyword')
    education = request.args.get('education')
    skills = request.args.getlist('skills')
    yoe = request.args.get('yoe')

    # keyword search will look through all of seeker's attributes and try to find a match.
    filters =[]
    if keyword:
        filters.append(
            Seeker.education.contains(keyword) |
            Seeker.yoe.contains(keyword) |
            Seeker.skills.any(Skill.name.contains(keyword)) |
            Seeker.name.contains(keyword) |
            Seeker.major.contains(keyword) |
            Seeker.prefered_work_mode.contains(keyword) |
            Seeker.email.contains(keyword) |
            Seeker.prefered_location.contains(keyword)
        )
    if education:
        filters.append(Seeker.education == education)
    if yoe:
        filters.append(Seeker.yoe >= int(yoe))
    if skills:
        filters.append(Seeker.skills.any(Skill.name.in_(skills)))

    # if filters exist, apply them to query, otherwise show all seekers
    if filters:
        seekers_query = Seeker.query.filter(*filters).all()
        if seekers_query == []:
            flash('No seekers found matching your criteria.')
    else:
        seekers_query = Seeker.query.all()

    skills = Skill.query.all()
    return render_template("talent-board.html",seekers=seekers_query, skills=skills)

@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Logged out successfully.")
    else:
        flash("You are not logged in.")
    return redirect('/')

if __name__=="__main__":
    with app.app_context():   
        db.create_all()
    app.run(debug=True)