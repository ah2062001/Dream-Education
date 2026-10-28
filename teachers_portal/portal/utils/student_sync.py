import os

import gspread
from django.conf import settings
from oauth2client.service_account import ServiceAccountCredentials

from portal.models import ClassUpdate, Student, TestScore

STUDENT_SHEET_NAME = "DreamEdu Student Progress System"

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    credentials_path = os.path.join(settings.BASE_DIR, "credentials.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, SCOPE)
    return gspread.authorize(creds)


def get_or_create_worksheet(workbook, title, rows="1000", cols="30"):
    try:
        return workbook.worksheet(title)
    except gspread.WorksheetNotFound:
        return workbook.add_worksheet(title=title, rows=rows, cols=cols)


def _update_sheet(workbook, title, rows):
    sheet = get_or_create_worksheet(workbook, title)
    sheet.clear()
    sheet.update(rows, value_input_option="USER_ENTERED")


def sync_students_master(workbook):
    rows = [[
        "StudentID", "Student_Name", "Student_Type", "Preferred_Name", "TeacherID", "Teacher_Name",
        "School_Name", "Year_Group", "Guardian_Name", "Guardian_Contact",
        "Notes", "Created_At"
    ]]

    for student in Student.objects.select_related("teacher").all():
        rows.append([
            str(student.id),
            student.full_name,
            student.get_student_type_display(),
            student.preferred_name,
            str(student.teacher.id),
            student.teacher.display_name,
            student.school_name,
            student.year_group,
            student.guardian_name,
            student.guardian_contact,
            student.notes,
            student.created_at.strftime("%Y-%m-%d %H:%M") if student.created_at else "",
        ])

    _update_sheet(workbook, "Students_Master", rows)


def sync_daily_progress(workbook):
    rows = [[
        "EntryID", "Date", "StudentID", "Student_Name", "Student_Type", "TeacherID", "Teacher_Name",
        "Subject/Title", "Update_Type", "Class_Work_Done", "Homework_Given",
        "Class_Marks", "Max_Marks", "Percentage", "Teacher_Comments",
        "Entered_At"
    ]]

    updates = ClassUpdate.objects.select_related("student", "student__teacher").all()
    for item in updates:
        rows.append([
            str(item.id),
            str(item.lesson_date),
            str(item.student.id),
            item.student.full_name,
            item.student.get_student_type_display(),
            str(item.student.teacher.id),
            item.student.teacher.display_name,
            item.title,
            item.get_update_type_display(),
            item.work_done,
            item.homework,
            item.class_marks if item.class_marks is not None else "",
            item.max_marks if item.max_marks is not None else "",
            item.percentage if item.percentage is not None else "",
            item.teacher_comment,
            item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "",
        ])

    _update_sheet(workbook, "Daily_Progress_Raw", rows)


def sync_weekly_assessments(workbook):
    rows = [[
        "AssessmentID", "Assessment_Date", "StudentID", "Student_Name", "Student_Type",
        "TeacherID", "Teacher_Name", "Assessment_Title", "Score",
        "Max_Score", "Percentage", "Remarks"
    ]]

    scores = TestScore.objects.select_related("student", "student__teacher").filter(period_type="weekly")
    for score in scores:
        rows.append([
            str(score.id),
            str(score.assessment_date),
            str(score.student.id),
            score.student.full_name,
            score.student.get_student_type_display(),
            str(score.student.teacher.id),
            score.student.teacher.display_name,
            score.assessment_name,
            score.score,
            score.total_marks,
            score.percentage,
            score.remarks,
        ])

    _update_sheet(workbook, "Weekly_Assessments", rows)


def sync_monthly_assessments(workbook):
    rows = [[
        "AssessmentID", "Assessment_Date", "Month", "Year", "StudentID",
        "Student_Name", "Student_Type", "TeacherID", "Teacher_Name", "Assessment_Title",
        "Score", "Max_Score", "Percentage", "Remarks"
    ]]

    scores = TestScore.objects.select_related("student", "student__teacher").filter(period_type="monthly")
    for score in scores:
        rows.append([
            str(score.id),
            str(score.assessment_date),
            score.assessment_date.strftime("%B"),
            score.assessment_date.year,
            str(score.student.id),
            score.student.full_name,
            score.student.get_student_type_display(),
            str(score.student.teacher.id),
            score.student.teacher.display_name,
            score.assessment_name,
            score.score,
            score.total_marks,
            score.percentage,
            score.remarks,
        ])

    _update_sheet(workbook, "Monthly_Assessments", rows)


def sync_students_workbook():
    client = get_client()
    workbook = client.open(STUDENT_SHEET_NAME)
    sync_students_master(workbook)
    sync_daily_progress(workbook)
    sync_weekly_assessments(workbook)
    sync_monthly_assessments(workbook)
