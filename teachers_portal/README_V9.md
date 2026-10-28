# Teachers Portal V9

V9 adds a second Google Sheets integration for student progress and marks.

## Google Sheet Workbooks

### 1. Schedule Workbook
Create a Google Sheet named exactly:

`DreamEdu Schedule System`

Recommended tabs:
- Schedule_Raw
- Weekly_Timetable_View
- Monthly_Calendar_View

### 2. Student Progress Workbook
Create a Google Sheet named exactly:

`DreamEdu Student Progress System`

Recommended tabs:
- Students_Master
- Daily_Progress_Raw
- Weekly_Assessments
- Monthly_Assessments

The Django database remains the main storage. Google Sheets are for synchronized views/backups.

## Credentials
Put `credentials.json` beside `manage.py`.

Share BOTH Google Sheets with the `client_email` from `credentials.json` as Editor.

## Run

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Manual Sync Test

```cmd
python manage.py shell
```

```python
from portal.utils.google_sync import sync_schedule_raw
from portal.utils.student_sync import sync_students_workbook
sync_schedule_raw()
sync_students_workbook()
```

## Automatic Sync
- Schedule data syncs when admin saves/deletes TeachingSchedule.
- Student progress and marks sync when teacher/admin saves/deletes Student, ClassUpdate, or TestScore.
