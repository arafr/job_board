# Database Structure

# Job Board Matching Algorithm:
Based on the below factors, a match score is given to each job posting. Top 10 jobs with highest match score is shown to seeker.

education 20
yoe 20
Skills 5 skills x 5 points each = 25
prefered_work_mode= 15
prefered_location= 20
Total = 100

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
python generate_skills.py
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
python3 generate_skills.py
```
```
python3 app.py
```

