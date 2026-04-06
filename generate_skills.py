from models import db, Skill
from app import app
def generate_skills():
    skills = [
        'project management',
        'Aws',
        'Azure',
        'GCP',
        'Kali Linux',
        'Nessus',
        'Burp suite',
        'IoT',
        'Microsoft Office',
        'SQL',
        'AI',
        'ML',
        'Mobile Dev',
        'Python',
        'Flask'
    ]
    for skill in skills:
        existing = Skill.query.filter_by(name=skill).first()
        if not existing:
            new_skill = Skill(name=skill)
            db.session.add(new_skill)
    db.session.commit()

with app.app_context():
    generate_skills()