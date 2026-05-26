from rapidfuzz import fuzz

job = Job.query.filter(Job.title.ilike("%software engineer%")).first()
search_match_ratio = fuzz.WRatio("software engineer", job.title)

if search_match_ratio > 70:
    return job