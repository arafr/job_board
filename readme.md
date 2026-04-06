# Database Structure

# Job Board Matching Algorithm:
1. First, check job posting database and make a list of jobs with matching criteria (education level, years of experience, work mode, location). Eliminate jobs with that don't match seeker.
2. From the previous list, based on number of matching skills (0-5), get top 10 most suitable jobs.

# Set up instructions:

### Windows:
```
python -m venv venv
```
```
venv\Scripts\activate
```
```
pip install -r requirements.txt
```
```
python app.py
```

### MacOS / Linux:
```
python3 -m venv venv
```
```
source venv/bin/activate
```
```
pip install -r requirements.txt
```
```
python3 app.py
```

