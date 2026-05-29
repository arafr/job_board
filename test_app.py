from app import app,db, Skill
import pytest
from templates.scripts.generate_skills import generate_skills

# FIXTURES 
@pytest.fixture()
def test_app():
    app.config.update({
        "TESTING": True,
        # temporary sqlite db for testing
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        
    })
    with app.app_context():
        db.create_all()

        # load up skills into db
        generate_skills()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(test_app):
    return test_app.test_client()

# ------------------------------------------ #

# UNIT TESTS

# check if homepage loads up successfully
def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200

# test password validation on employer sign up page
def test_password_validation_employer(client):
    response = client.post("/signup-employer", data={
        "email": "test-employer@gmail.com",
        "password": "test12",
    },follow_redirects=True)
    html = response.get_data(as_text=True)
    assert 'Password must be at least 8 characters long' in html

# test if skills are loaded into app
def test_loaded_skills(test_app):
    with test_app.app_context():
        skills = Skill.query.all()
        skill_names = [s.name for s in skills]
        assert "Python" in skill_names
        assert "AWS" in skill_names
        assert "Flask" in skill_names

# ------------------------------------------ #

# INTEGRATION TESTS

# check employer authentication
@pytest.fixture()
def test_employer_authentication(client):
    # log out any sessions first
    client.get("/logout")

    response = client.post("/signup-employer", data={
        "email": "test-employer@gmail.com",
        "password": "test-password",
    },follow_redirects=True)
    html = response.get_data(as_text=True)
    assert 'Successfully created account' in html

    response = client.post("/login-employer", data={
        # login with the previously created credentials
        "email": "test-employer@gmail.com",
        "password": "test-password",
    },follow_redirects=True)
    html = response.get_data(as_text=True)
    assert 'Login successful' in html

    # the create job requires user to be authenticated
    # the get request to create page will only be successful if user is logged in
    response = client.get("/create-job")
    assert response.status_code==200

    # same thing for talent board page
    response = client.get("/talent-board")
    assert response.status_code==200

# check seeker authentication
@pytest.fixture() # turned this into a fixture so we can reuse this function in other tests
def test_seeker_authentication(client):
    # log out any sessions first
    client.get("/logout")
    response = client.post("/signup-seeker", data={
        "email": "test-seeker@gmail.com",
        "name": "Test Tester",
        "password": "test-password",
        "education": "high school",
        "major": "Test Major",
        "yoe": 1,
        "prefered_work_mode": "remote",
        "prefered_location": "Sydney",
        "skills": ["Python","AWS","IoT"],
    },follow_redirects=True)
    html = response.get_data(as_text=True)
    assert 'Successfully created account' in html

    response = client.post("/login-seeker", data={
        # login with the previously created credentials
        "email": "test-seeker@gmail.com",
        "password": "test-password",
    },follow_redirects=True)
    html = response.get_data(as_text=True)
    assert 'Login successful' in html

    # the job board requires user to be authenticated
    # the get request to job board page will only be successful if user is logged in
    response = client.get("/job-board")
    assert response.status_code==200

def test_seeker_logout(client,test_seeker_authentication):
    # check log out
    response = client.get("/logout")

    # after logging out, these login required pages should give back 401 (unauthorized)
    response = client.get("/job-board")
    assert response.status_code==401

@pytest.fixture()
def test_job_creation(client,test_employer_authentication):
    response = client.post("/create-job", data={
        "title": "Test Software Engineer",
        "company_name": "Test Company",
        "company_email": "test-company@gmail.com",
        "description": "Test description",
        "education": "masters degree",
        "skills": ['Python','AWS','GCP'],
        "yoe": 3,
        "job_type": "full-time",
        "work_mode": "remote",
        "location": "Sydney",
    },follow_redirects=True)
    html = response.get_data(as_text=True)
    assert 'Job created successfully' in html

# check job details page
def test_job_details(client,test_job_creation):
    response = client.get("/job-details/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Test Software Engineer' in html
    assert "test-company@gmail.com" in html
    assert "Test description" in html

# test talent board filters
def test_job_board_filters(client, test_job_creation,test_seeker_authentication):
    response = client.get("/job-board?title=enginer")
    html = response.get_data(as_text=True)
    assert 'No jobs found.' not in html

    response = client.get("/job-board?title=happydappyyappy")
    html = response.get_data(as_text=True)
    assert 'No jobs found.' in html

# test talent board filters
# first fixture will create a seeker profile
# 2nd fixture will create and log us in as an employer to access the talent board
def test_talent_board_filters(client,test_seeker_authentication,test_employer_authentication):
    response = client.get("/talent-board?keyword=&education=masters+degree&yoe=3")
    html = response.get_data(as_text=True)
    assert 'No seekers found.' in html

    response = client.get("/talent-board?keyword=&education=high+school&yoe=1")
    html = response.get_data(as_text=True)
    assert 'Test Tester' in html

# test membership
# we use a for loop to create 11 jobs
# we create 2 seeker profiles, one with no membership and one with membership
# the seeker with no membership should see 10 jobs
# the seeker with membership should see 10+ jobs (11 in our case)
def test_membership(client,test_employer_authentication):
    # this for loop with create 11 jobs
    for i in range(1,12):
        response = client.post("/create-job", data={
            "title": "Job"+str(i), # job1, job2...job11
            "company_name": "Test Company",
            "company_email": "test-company@gmail.com",
            "description": "Test description",
            "education": "masters degree",
            "skills": ['Python','AWS','GCP'],
            "yoe": 3,
            "job_type": "full-time",
            "work_mode": "remote",
            "location": "Sydney",
        })

    # now login as a seeker with no membership
    # log out any sessions first
    client.get("/logout")
    response = client.post("/signup-seeker", data={
        "email": "test-seeker@gmail.com",
        "name": "Test Tester",
        "password": "test-password",
        "education": "high school",
        "major": "Test Major",
        "yoe": 1,
        "prefered_work_mode": "remote",
        "prefered_location": "Sydney",
        "skills": ["Python","AWS","IoT"],
    })
    response = client.post("/login-seeker", data={
        # login with the previously created credentials
        "email": "test-seeker@gmail.com",
        "password": "test-password",
    })

    # now we go to job board page, we should only see 10 jobs, not 11.
    response = client.get("/job-board")
    html = response.get_data(as_text=True)
    assert 'Job11' not in html

    # now we create a seeker profile with membership

    # log out any sessions first
    client.get("/logout")
    response = client.post("/signup-seeker", data={
        "email": "test-seeker-membership@gmail.com",
        "name": "Test Tester",
        "password": "test-password",
        "education": "high school",
        "major": "Test Major",
        "yoe": 1,
        "prefered_work_mode": "remote",
        "prefered_location": "Sydney",
        "skills": ["Python","AWS","IoT"],
        'membership': True,
    })
    response = client.post("/login-seeker", data={
        # login with the previously created credentials
        "email": "test-seeker-membership@gmail.com",
        "password": "test-password",
    })

    # now we go to job board page, we should only see the 11th job as well.
    response = client.get("/job-board")
    html = response.get_data(as_text=True)
    assert 'Job11' in html

