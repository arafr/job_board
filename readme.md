# Employer Worflow
1. Employer creates an account and logs in. 
2. They create a job posting.
3. Then they view the job posting details and get suggested matching candidates for the job. They will see 10 best candidates max if they are not a member, while members can see unlimited candidate profiles.
4. Employers can also visit the talent board to view all seekers on the platform. They can use search and filter to find seekers.

# Seeker Worflow
1. Seeker creates an account and logs in.
2. They visit the job board to view all jobs. They can search and filter for their preferred jobs. The best jobs for you section shows them 10 best jobs max if they are not a member, unlimited jobs if they are.
3. Seeker can click on a job and view full details of the job posting.

# Matching Algorithm (for finding best seekers and jobs):
Based on the below factors, a match score is calculated for each job posting and seeker in relation to each other.

Education match 20 points

YOE 20

5 Skills x 5 points each = 25

Work mode match 15

Location match 20

Total 100

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

## Database
![UML diagram.](/uml/updated_uml.png "UML diagram")
