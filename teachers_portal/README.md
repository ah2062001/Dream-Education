# Teachers Portal Project v7

Stability release for the Dream Edu Teachers Portal.

## What v7 fixes

- Cleaner login/logout flow
- Logout no longer gives confusing 403 errors during demos
- Back-button / cached logout issues are reduced
- Admin users are safely redirected to the admin overview instead of teacher-only pages
- Teacher-only pages redirect cleanly if opened by a non-teacher account
- Login redirects to the correct role-based landing page
- Added on-screen messages for login/logout/access guidance

## Included features

- Django-admin-style teacher UI
- Login/logout and account switching
- Admin-managed teacher profiles
- Admin-managed recurring teaching schedules
- Monthly calendar page for teachers
- Teacher dashboard with next-class timing
- Teacher-managed students
- Daily / weekly / monthly progress updates
- Weekly / monthly test scores
- Edit test scores
- Premium downloadable PDF student progress reports

## Run locally

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open:

- Portal: http://127.0.0.1:8000/login/
- Admin: http://127.0.0.1:8000/admin/

## Demo accounts

- admin / admin12345
- ameer / teacher12345
- sun / teacher12345

## Recommended testing flow

1. Log in as admin.
2. Open `/admin/` and add/update teaching schedules.
3. Click **Log out** from the top bar.
4. Log in as `ameer` or `sun`.
5. Open dashboard and monthly schedule.
6. Check student pages and PDF report download.

## Admin schedule setup

Log in as admin, open `/admin/`, then create `Teaching schedules`.
Select teacher, subject, student details, date range, class time, and one or more weekdays.
Selecting two weekdays means two classes per week.

## PDF reports

Log in as a teacher, open any student profile, then click **Download PDF Report**.
