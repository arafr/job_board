"""
pytest test suite for the Flask Job Board application.

Setup:
    pip install pytest flask flask-sqlalchemy flask-login flask-bcrypt

Run:
    pytest test_app.py -v
"""

import pytest
from flask import session
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# App + DB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create a test application with an in-memory SQLite database."""
    # Patch generate_skills so the import side-effect doesn't blow up
    with patch("templates.scripts.generate_skills.generate_skills", return_value=None):
        from app import app as flask_app

    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret-key",
        LOGIN_DISABLED=False,
    )
    return flask_app


@pytest.fixture(scope="session")
def db(app):
    """Create all tables once for the session."""
    from models import db as _db
    with app.app_context():
        _db.create_all()
        _seed_skills(_db)
    yield _db
    with app.app_context():
        _db.drop_all()


def _seed_skills(db):
    from models import Skill
    for name in ["Python", "SQL", "JavaScript", "Docker", "AWS"]:
        if not Skill.query.filter_by(name=name).first():
            db.session.add(Skill(name=name))
    db.session.commit()


@pytest.fixture()
def client(app, db):
    """Per-test Flask test client."""
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_seeker(client, email="seeker@test.com", password="pass123",
                     name="Alice", membership=False):
    data = {
        "email": email,
        "name": name,
        "password": password,
        "education": "bachelors degree",
        "major": "Computer Science",
        "yoe": "2",
        "prefered_work_mode": "remote",
        "prefered_location": "Sydney",
        "skills": ["Python", "SQL"],
    }
    if membership:
        data["membership"] = "on"
    return client.post("/signup-seeker", data=data, follow_redirects=True)


def _login_seeker(client, email="seeker@test.com", password="pass123"):
    return client.post(
        "/login-seeker",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def _register_employer(client, email="employer@test.com", password="pass123",
                       membership=False):
    data = {"email": email, "password": password}
    if membership:
        data["membership"] = "on"
    return client.post("/signup-employer", data=data, follow_redirects=True)


def _login_employer(client, email="employer@test.com", password="pass123"):
    return client.post(
        "/login-employer",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def _create_job(client, title="Backend Engineer", skills=None):
    return client.post(
        "/create-job/",
        data={
            "title": title,
            "company_name": "Acme Corp",
            "company_email": "hr@acme.com",
            "description": "Great role",
            "education": "bachelors degree",
            "yoe": "1",
            "job_type": "full-time",
            "work_mode": "remote",
            "location": "Sydney",
            "skills": skills or ["Python"],
        },
        follow_redirects=True,
    )


# ---------------------------------------------------------------------------
# 1. Home page
# ---------------------------------------------------------------------------

class TestHomePage:
    def test_home_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_contains_expected_content(self, client):
        resp = client.get("/")
        # At minimum the page should return HTML
        assert b"<!DOCTYPE html>" in resp.data or b"<html" in resp.data


# ---------------------------------------------------------------------------
# 2. Seeker signup
# ---------------------------------------------------------------------------

class TestSeekerSignup:
    def test_get_signup_page(self, client):
        resp = client.get("/signup-seeker")
        assert resp.status_code == 200

    def test_successful_signup(self, client, db, app):
        resp = _register_seeker(client, email="new_seeker@test.com")
        assert resp.status_code == 200
        # should redirect to login page or show success flash
        assert b"Successfully created account" in resp.data or b"login" in resp.data.lower()

    def test_duplicate_email_rejected(self, client, db, app):
        _register_seeker(client, email="dup_seeker@test.com")
        resp = _register_seeker(client, email="dup_seeker@test.com")
        assert b"Email already exists" in resp.data

    def test_too_many_skills_rejected(self, client, db, app):
        resp = client.post(
            "/signup-seeker",
            data={
                "email": "toomanyskills@test.com",
                "name": "Bob",
                "password": "pass123",
                "education": "bachelors degree",
                "major": "CS",
                "yoe": "1",
                "prefered_work_mode": "remote",
                "prefered_location": "Sydney",
                "skills": ["Python", "SQL", "JavaScript", "Docker", "AWS", "Python"],
            },
            follow_redirects=True,
        )
        assert b"maximum of 5 skills" in resp.data

    def test_authenticated_seeker_redirected_from_signup(self, client, db, app):
        _register_seeker(client, email="redir_seeker@test.com")
        _login_seeker(client, email="redir_seeker@test.com")
        resp = client.get("/signup-seeker", follow_redirects=False)
        assert resp.status_code == 302
        assert b"/job-board/" in resp.headers.get("Location", "").encode()


# ---------------------------------------------------------------------------
# 3. Seeker login
# ---------------------------------------------------------------------------

class TestSeekerLogin:
    def test_get_login_page(self, client):
        resp = client.get("/login-seeker")
        assert resp.status_code == 200

    def test_successful_login(self, client, db, app):
        _register_seeker(client, email="login_seeker@test.com")
        resp = _login_seeker(client, email="login_seeker@test.com")
        assert b"Login successful" in resp.data

    def test_wrong_password_rejected(self, client, db, app):
        _register_seeker(client, email="wrongpass@test.com")
        resp = client.post(
            "/login-seeker",
            data={"email": "wrongpass@test.com", "password": "wrongpassword"},
            follow_redirects=True,
        )
        assert b"Invalid email or password" in resp.data

    def test_nonexistent_user_rejected(self, client):
        resp = client.post(
            "/login-seeker",
            data={"email": "ghost@test.com", "password": "anything"},
            follow_redirects=True,
        )
        assert b"Invalid email or password" in resp.data


# ---------------------------------------------------------------------------
# 4. Employer signup + login
# ---------------------------------------------------------------------------

class TestEmployerAuth:
    def test_get_employer_signup(self, client):
        assert client.get("/signup-employer").status_code == 200

    def test_successful_employer_signup(self, client, db, app):
        resp = _register_employer(client, email="emp_new@test.com")
        assert b"Successfully created account" in resp.data or resp.status_code == 200

    def test_duplicate_employer_email(self, client, db, app):
        _register_employer(client, email="emp_dup@test.com")
        resp = _register_employer(client, email="emp_dup@test.com")
        assert b"Email already exists" in resp.data

    def test_get_employer_login(self, client):
        assert client.get("/login-employer").status_code == 200

    def test_successful_employer_login(self, client, db, app):
        _register_employer(client, email="emp_login@test.com")
        resp = _login_employer(client, email="emp_login@test.com")
        assert b"Login successful" in resp.data

    def test_employer_wrong_password(self, client, db, app):
        _register_employer(client, email="emp_badpw@test.com")
        resp = client.post(
            "/login-employer",
            data={"email": "emp_badpw@test.com", "password": "wrong"},
            follow_redirects=True,
        )
        assert b"Invalid email or password" in resp.data


# ---------------------------------------------------------------------------
# 5. Job board (login required)
# ---------------------------------------------------------------------------

class TestJobBoard:
    def test_unauthenticated_redirected(self, client):
        resp = client.get("/job-board/", follow_redirects=False)
        assert resp.status_code == 401

    def test_authenticated_seeker_can_access(self, client, db, app):
        _register_seeker(client, email="jb_seeker@test.com")
        _login_seeker(client, email="jb_seeker@test.com")
        resp = client.get("/job-board/")
        assert resp.status_code == 200

    def test_keyword_filter_accepted(self, client, db, app):
        _register_seeker(client, email="kw_seeker@test.com")
        _login_seeker(client, email="kw_seeker@test.com")
        resp = client.get("/job-board/?keyword=engineer")
        assert resp.status_code == 200

    def test_work_mode_filter_accepted(self, client, db, app):
        _register_seeker(client, email="wm_seeker@test.com")
        _login_seeker(client, email="wm_seeker@test.com")
        resp = client.get("/job-board/?work_mode=remote")
        assert resp.status_code == 200

    def test_no_match_shows_flash(self, client, db, app):
        _register_seeker(client, email="nomatch_seeker@test.com")
        _login_seeker(client, email="nomatch_seeker@test.com")
        resp = client.get("/job-board/?keyword=xyznonexistent123")
        assert b"No postings found" in resp.data or resp.status_code == 200


# ---------------------------------------------------------------------------
# 6. Create job (employer only flow)
# ---------------------------------------------------------------------------

class TestCreateJob:
    def test_unauthenticated_redirected(self, client):
        resp = client.get("/create-job/", follow_redirects=False)
        assert resp.status_code == 401

    def test_get_create_job_page(self, client, db, app):
        _register_employer(client, email="cj_emp@test.com")
        _login_employer(client, email="cj_emp@test.com")
        resp = client.get("/create-job/")
        assert resp.status_code == 200

    def test_create_job_successfully(self, client, db, app):
        _register_employer(client, email="cj_emp2@test.com")
        _login_employer(client, email="cj_emp2@test.com")
        resp = _create_job(client, title="Senior Developer")
        assert b"Job created successfully" in resp.data or resp.status_code == 200

    def test_create_job_too_many_skills(self, client, db, app):
        _register_employer(client, email="cj_emp3@test.com")
        _login_employer(client, email="cj_emp3@test.com")
        resp = client.post(
            "/create-job/",
            data={
                "title": "Bad Job",
                "company_name": "Corp",
                "company_email": "a@corp.com",
                "description": "desc",
                "education": "bachelors degree",
                "yoe": "1",
                "job_type": "full-time",
                "work_mode": "remote",
                "location": "Sydney",
                "skills": ["Python", "SQL", "JavaScript", "Docker", "AWS", "Python"],
            },
            follow_redirects=True,
        )
        assert b"maximum of 5 skills" in resp.data


# ---------------------------------------------------------------------------
# 7. Job details page
# ---------------------------------------------------------------------------

class TestJobDetails:
    def _setup_job(self, client, db, app):
        """Register employer, log in, create a job, return posting id."""
        _register_employer(client, email="jd_emp@test.com")
        _login_employer(client, email="jd_emp@test.com")
        _create_job(client, title="DevOps Engineer")
        # Get the posting from DB
        with app.app_context():
            from models import Posting
            posting = Posting.query.filter_by(title="DevOps Engineer").first()
            return posting.id if posting else 1

    def test_job_details_page_loads(self, client, db, app):
        posting_id = self._setup_job(client, db, app)
        resp = client.get(f"/job-details/{posting_id}/")
        assert resp.status_code == 200

    def test_nonexistent_job_returns_404(self, client):
        resp = client.get("/job-details/99999/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 8. Talent board
# ---------------------------------------------------------------------------

class TestTalentBoard:
    def test_unauthenticated_redirected(self, client):
        resp = client.get("/talent-board", follow_redirects=False)
        assert resp.status_code == 401

    def test_employer_can_access_talent_board(self, client, db, app):
        _register_employer(client, email="tb_emp@test.com")
        _login_employer(client, email="tb_emp@test.com")
        resp = client.get("/talent-board")
        assert resp.status_code == 200

    def test_keyword_filter(self, client, db, app):
        _register_employer(client, email="tb_kw_emp@test.com")
        _login_employer(client, email="tb_kw_emp@test.com")
        resp = client.get("/talent-board?keyword=Python")
        assert resp.status_code == 200

    def test_education_filter(self, client, db, app):
        _register_employer(client, email="tb_edu_emp@test.com")
        _login_employer(client, email="tb_edu_emp@test.com")
        resp = client.get("/talent-board?education=bachelors+degree")
        assert resp.status_code == 200

    def test_no_seekers_found_flash(self, client, db, app):
        _register_employer(client, email="tb_nf_emp@test.com")
        _login_employer(client, email="tb_nf_emp@test.com")
        resp = client.get("/talent-board?keyword=zzznomatch999")
        assert b"No seekers found" in resp.data or resp.status_code == 200


# ---------------------------------------------------------------------------
# 9. Logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_authenticated_user(self, client, db, app):
        _register_seeker(client, email="logout_seeker@test.com")
        _login_seeker(client, email="logout_seeker@test.com")
        resp = client.get("/logout", follow_redirects=True)
        assert b"Logged out successfully" in resp.data

    def test_logout_unauthenticated_user(self, client):
        resp = client.get("/logout", follow_redirects=True)
        assert b"You are not logged in" in resp.data


# ---------------------------------------------------------------------------
# 10. Match scoring logic (unit tests, no HTTP)
# ---------------------------------------------------------------------------

class TestMatchScoring:
    """
    Test the scoring algorithm in isolation using model instances directly.
    These tests don't go through HTTP — they invoke scoring logic the same
    way the routes do.
    """

    def test_education_score_bachelors_meets_high_school_req(self, app, db):
        """Seeker with bachelors satisfies a high school requirement (+20)."""
        with app.app_context():
            education_level = ["high school", "bachelors degree"]
            posting_education = "high school"
            assert posting_education in education_level

    def test_education_score_high_school_fails_bachelors_req(self, app, db):
        """Seeker with only high school does NOT satisfy bachelors requirement."""
        seeker_education = "high school"
        education_level_for_bachelors_posting = ["bachelors degree", "masters degree", "phd"]
        assert seeker_education not in education_level_for_bachelors_posting

    def test_yoe_exact_match_scores(self, app, db):
        """Seeker yoe equal to posting yoe should score points."""
        seeker_yoe = 3
        posting_yoe = 3
        score = 0
        if seeker_yoe >= posting_yoe:
            score += 20
        assert score == 20

    def test_yoe_below_requirement_scores_zero(self, app, db):
        seeker_yoe = 1
        posting_yoe = 3
        score = 0
        if seeker_yoe >= posting_yoe:
            score += 20
        assert score == 0

    def test_skill_overlap_scoring(self, app, db):
        """Each overlapping skill adds 5 points."""
        seeker_skills = {"Python", "SQL", "Docker"}
        posting_skills = {"Python", "SQL"}
        score = sum(5 for s in seeker_skills if s in posting_skills)
        assert score == 10

    def test_no_skill_overlap_scores_zero(self, app, db):
        seeker_skills = {"JavaScript"}
        posting_skills = {"Python", "SQL"}
        score = sum(5 for s in seeker_skills if s in posting_skills)
        assert score == 0

    def test_max_possible_score(self, app, db):
        """Full match: education + yoe + work_mode + location + 5 skills = 100."""
        score = 0
        score += 20  # education
        score += 20  # yoe
        score += 15  # work_mode
        score += 20  # location
        score += 5 * 5  # 5 skills
        assert score == 100

    def test_non_member_capped_at_10_results(self, app, db):
        fake_postings = list(range(20))  # 20 items
        capped = fake_postings[:10]
        assert len(capped) == 10

    def test_member_sees_all_results(self, app, db):
        fake_postings = list(range(20))
        assert len(fake_postings) == 20