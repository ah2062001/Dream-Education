import calendar
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import ClassUpdateForm, StudentForm, TestScoreForm
from .models import ClassUpdate, Student, TeacherProfile, TeachingSchedule, TestScore



def _safe_sync_students_workbook():
    try:
        from portal.utils.student_sync import sync_students_workbook
        sync_students_workbook()
    except Exception as e:
        print('Google Sheets student sync failed:', e)



DAY_NAME_TO_INDEX = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
    'Saturday': 5,
    'Sunday': 6,
}


def is_admin(user):
    return user.is_superuser or user.is_staff


def teacher_required(user):
    return hasattr(user, 'teacher_profile')


def _next_occurrence_for_schedule(schedule, now=None):
    now = now or timezone.localtime()
    tz = timezone.get_current_timezone()
    today = now.date()
    upcoming = []
    for day_name in schedule.weekday_list:
        target_weekday = DAY_NAME_TO_INDEX.get(day_name, 0)
        days_ahead = (target_weekday - today.weekday()) % 7
        candidate_date = today + timedelta(days=days_ahead)
        if candidate_date < schedule.start_date:
            candidate_date = schedule.start_date
            offset = (target_weekday - candidate_date.weekday()) % 7
            candidate_date = candidate_date + timedelta(days=offset)
        candidate_dt = timezone.make_aware(datetime.combine(candidate_date, schedule.start_time), tz)
        if candidate_dt <= now:
            candidate_date += timedelta(days=7)
            candidate_dt = timezone.make_aware(datetime.combine(candidate_date, schedule.start_time), tz)
        if schedule.start_date <= candidate_dt.date() <= schedule.end_date:
            upcoming.append(candidate_dt)
    return min(upcoming) if upcoming else None


def _format_time_until(dt, now=None):
    now = now or timezone.localtime()
    delta = dt - now
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return 'Starting now'
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return 'In ' + ' '.join(parts[:2])


def _build_month_calendar(teacher, year, month):
    cal = calendar.Calendar(firstweekday=0)
    month_name = calendar.month_name[month]
    schedules = list(teacher.teaching_schedules.all())
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_cells = []
        for day in week:
            day_events = []
            if day.month == month:
                day_name = calendar.day_name[day.weekday()]
                for schedule in schedules:
                    if day_name in schedule.weekday_list and schedule.start_date <= day <= schedule.end_date:
                        day_events.append(schedule)
                day_events.sort(key=lambda e: e.start_time)
            week_cells.append({
                'date': day,
                'in_month': day.month == month,
                'entries': day_events,
                'is_today': day == timezone.localdate(),
            })
        weeks.append(week_cells)

    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1

    return {
        'weeks': weeks,
        'month_name': month_name,
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }


@never_cache
@csrf_exempt
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Log out safely from both portal and admin-related sessions.

    Accepting GET as well as POST avoids confusing 403 errors during demos when
    the browser back button or an old cached logout page is used.
    """
    logout(request)
    messages.success(request, 'You have been logged out. Please sign in again.')
    return redirect('login')


@login_required
def landing(request):
    if is_admin(request.user):
        teacher_count = TeacherProfile.objects.count()
        student_count = Student.objects.count()
        schedule_count = TeachingSchedule.objects.count()
        return render(request, 'portal/admin_overview.html', {
            'teacher_count': teacher_count,
            'student_count': student_count,
            'schedule_count': schedule_count,
            'recent_teachers': TeacherProfile.objects.all()[:8],
        })
    if teacher_required(request.user):
        return redirect('portal:teacher_dashboard')
    return render(request, 'portal/no_role.html')


@login_required
def teacher_dashboard(request):
    if not teacher_required(request.user):
        messages.warning(request, 'Please log in with a teacher account to access that page.')
        return redirect('portal:landing')
    teacher = request.user.teacher_profile
    students = teacher.students.all()
    schedules = teacher.teaching_schedules.all()
    stats = teacher.students.aggregate(total_students=Count('id'))

    next_schedule = None
    next_class_time = None
    upcoming = []
    for schedule in schedules:
        dt = _next_occurrence_for_schedule(schedule)
        if dt:
            upcoming.append((dt, schedule))
    if upcoming:
        next_class_time, next_schedule = sorted(upcoming, key=lambda item: item[0])[0]

    return render(request, 'portal/teacher_dashboard.html', {
        'teacher': teacher,
        'students': students,
        'schedule': schedules[:4],
        'total_students': stats['total_students'] or 0,
        'next_schedule': next_schedule,
        'next_class_time': next_class_time,
        'next_class_in': _format_time_until(next_class_time) if next_class_time else 'No classes scheduled',
    })


@login_required
def schedule_calendar(request):
    if not teacher_required(request.user):
        messages.warning(request, 'Please log in with a teacher account to access that page.')
        return redirect('portal:landing')
    teacher = request.user.teacher_profile
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if month < 1 or month > 12:
            raise ValueError
    except ValueError:
        year, month = today.year, today.month

    context = {'teacher': teacher, **_build_month_calendar(teacher, year, month)}
    return render(request, 'portal/schedule_calendar.html', context)


@login_required
def student_create(request):
    if not teacher_required(request.user):
        messages.warning(request, 'Please log in with a teacher account to access that page.')
        return redirect('portal:landing')
    teacher = request.user.teacher_profile
    form = StudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        student = form.save(commit=False)
        student.teacher = teacher
        student.save()
        _safe_sync_students_workbook()
        return redirect('portal:student_detail', pk=student.pk)
    return render(request, 'portal/student_form.html', {'form': form, 'mode': 'create'})


@login_required
def student_detail(request, pk):
    if not teacher_required(request.user):
        messages.warning(request, 'Please log in with a teacher account to access that page.')
        return redirect('portal:landing')
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, pk=pk, teacher=teacher)
    return render(request, 'portal/student_detail.html', {
        'student': student,
        'updates': student.updates.all(),
        'scores': student.test_scores.all(),
    })


@login_required
def add_update(request, pk):
    if not teacher_required(request.user):
        messages.warning(request, 'Please log in with a teacher account to access that page.')
        return redirect('portal:landing')
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, pk=pk, teacher=teacher)
    form = ClassUpdateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        update = form.save(commit=False)
        update.student = student
        update.save()
        _safe_sync_students_workbook()
        return redirect('portal:student_detail', pk=student.pk)
    return render(request, 'portal/update_form.html', {'form': form, 'student': student})


@login_required
def add_score(request, pk):
    if not teacher_required(request.user):
        messages.warning(request, 'Please log in with a teacher account to access that page.')
        return redirect('portal:landing')
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, pk=pk, teacher=teacher)
    form = TestScoreForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        score = form.save(commit=False)
        score.student = student
        score.save()
        _safe_sync_students_workbook()
        return redirect('portal:student_detail', pk=student.pk)
    return render(request, 'portal/score_form.html', {'form': form, 'student': student})


@login_required
def edit_score(request, pk, score_id):
    if not teacher_required(request.user):
        messages.warning(request, 'Please log in with a teacher account to access that page.')
        return redirect('portal:landing')
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, pk=pk, teacher=teacher)
    score = get_object_or_404(TestScore, pk=score_id, student=student)
    form = TestScoreForm(request.POST or None, instance=score)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _safe_sync_students_workbook()
        return redirect('portal:student_detail', pk=student.pk)
    return render(request, 'portal/score_form.html', {'form': form, 'student': student, 'mode': 'edit'})


@login_required

# --- V10 CLEAN REPORT HELPERS ---
def _program_label(student):
    return dict(Student.PROGRAM_CHOICES).get(student.student_type, student.student_type.title())


def _grade_from_percentage(percentage):
    if percentage is None:
        return "N/A"
    if percentage >= 90:
        return "A"
    if percentage >= 80:
        return "B"
    if percentage >= 70:
        return "C"
    if percentage >= 60:
        return "D"
    return "Needs Support"


def _score_rows(scores):
    rows = [["Date", "Type", "Assessment", "Score", "%", "Grade"]]
    for score in scores:
        pct = score.percentage
        rows.append([
            str(score.assessment_date),
            score.get_period_type_display(),
            score.assessment_name,
            f"{score.score}/{score.total_marks}",
            f"{pct}%" if pct is not None else "N/A",
            _grade_from_percentage(pct),
        ])
    if len(rows) == 1:
        rows.append(["-", "-", "No assessment records yet", "-", "-", "-"])
    return rows


def _add_report_header(elements, student, styles):
    import os
    from django.conf import settings

    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "dream_education_logo.png")
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1.9 * inch, height=0.95 * inch)
        img.hAlign = "CENTER"
        elements.append(img)
        elements.append(Spacer(1, 6))

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        textColor=colors.HexColor("#0F3D75"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=14,
    )
    elements.append(Paragraph(f"{_program_label(student)} Progress Report", title_style))
    elements.append(Paragraph("Dream Education — Student Academic Record", subtitle_style))


def _student_info_table(student):
    data = [
        ["Student Name", student.full_name],
        ["Preferred Name", student.preferred_name or "-"],
        ["Program / Type", _program_label(student)],
        ["Teacher", student.teacher.display_name],
        ["School / Level", f"{student.school_name or '-'} / {student.year_group or '-'}"],
        ["Guardian", student.guardian_name or "-"],
    ]
    table = Table(data, colWidths=[1.7 * inch, 4.7 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2FF")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0F3D75")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C9D8EE")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6E1F2")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _assessment_table(scores):
    table = Table(_score_rows(scores), colWidths=[0.95*inch, 0.9*inch, 2.2*inch, 0.8*inch, 0.7*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F3D75")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C9D8EE")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6E1F2")),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FBFF")),
    ]))
    return table


def _add_recent_updates(elements, updates, styles):
    section_style = ParagraphStyle(
        "RecentUpdatesTitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0F3D75"),
        spaceBefore=12,
        spaceAfter=6,
    )
    elements.append(Paragraph("Recent Learning Updates", section_style))
    if not updates:
        elements.append(Paragraph("No recent progress comments have been added yet.", styles["Normal"]))
        return
    for u in updates[:5]:
        elements.append(Paragraph(f"<b>{u.lesson_date} — {u.title}</b>", styles["Normal"]))
        elements.append(Paragraph(f"Work done: {u.work_done}", styles["Normal"]))
        if u.teacher_comment:
            elements.append(Paragraph(f"Teacher comment: {u.teacher_comment}", styles["Normal"]))
        elements.append(Spacer(1, 6))


def _add_ielts_breakdown(elements, scores, updates, styles):
    section_style = ParagraphStyle(
        "IELTSSection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0F3D75"),
        spaceBefore=10,
        spaceAfter=6,
    )
    elements.append(Paragraph("IELTS Skill Breakdown", section_style))

    skill_keywords = {
        "Listening": ["listening", "listen"],
        "Reading": ["reading", "read"],
        "Writing": ["writing", "write"],
        "Speaking": ["speaking", "speak"],
    }

    data = [["Skill", "Latest Score / Band", "Teacher Note"]]
    for skill, keywords in skill_keywords.items():
        matched_scores = [
            s for s in scores
            if any(k in s.assessment_name.lower() for k in keywords)
        ]
        latest_score = matched_scores[0] if matched_scores else None
        matched_updates = [
            u for u in updates
            if any(k in (u.title + " " + u.work_done + " " + u.teacher_comment).lower() for k in keywords)
        ]
        note = matched_updates[0].teacher_comment if matched_updates and matched_updates[0].teacher_comment else "To be updated"
        data.append([
            skill,
            f"{latest_score.score}/{latest_score.total_marks}" if latest_score else "To be updated",
            note,
        ])

    table = Table(data, colWidths=[1.2*inch, 1.6*inch, 3.6*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F3D75")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C9D8EE")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6E1F2")),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FBFF")),
    ]))
    elements.append(table)


def _add_subject_specific_section(elements, student, styles):
    section_style = ParagraphStyle(
        "SubjectSection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0F3D75"),
        spaceBefore=10,
        spaceAfter=6,
    )
    elements.append(Paragraph(f"{_program_label(student)} Focus Areas", section_style))

    if student.student_type == "math":
        points = [
            "Concept understanding and accuracy",
            "Problem-solving approach",
            "Algebra / geometry / calculation practice",
            "Homework consistency",
        ]
    elif student.student_type == "science":
        points = [
            "Theory understanding",
            "Scientific reasoning",
            "Practical / experiment awareness",
            "Use of correct scientific vocabulary",
        ]
    elif student.student_type == "english":
        points = [
            "Reading comprehension",
            "Grammar accuracy",
            "Vocabulary development",
            "Writing clarity and expression",
        ]
    else:
        points = ["Overall academic progress", "Homework consistency", "Class participation"]

    data = [["Area", "Status"]]
    for p in points:
        data.append([p, "See teacher comments and assessment records"])

    table = Table(data, colWidths=[2.6*inch, 3.8*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F3D75")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C9D8EE")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6E1F2")),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FBFF")),
    ]))
    elements.append(table)


def download_report(request, pk):
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    student = get_object_or_404(Student, pk=pk, teacher=teacher)
    scores = list(student.scores.all().order_by("-assessment_date"))
    updates = list(student.updates.all().order_by("-lesson_date", "-created_at"))

    response = HttpResponse(content_type="application/pdf")
    filename = f"{student.full_name.replace(' ', '_')}_{student.student_type}_report.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=35,
        bottomMargin=35,
    )
    styles = getSampleStyleSheet()
    elements = []

    _add_report_header(elements, student, styles)
    elements.append(_student_info_table(student))
    elements.append(Spacer(1, 14))

    if student.student_type == "ielts":
        _add_ielts_breakdown(elements, scores, updates, styles)
        elements.append(Spacer(1, 12))
    else:
        _add_subject_specific_section(elements, student, styles)
        elements.append(Spacer(1, 12))

    section_style = ParagraphStyle(
        "AssessmentSection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0F3D75"),
        spaceBefore=10,
        spaceAfter=6,
    )

    elements.append(Paragraph("Assessment Summary", section_style))
    elements.append(_assessment_table(scores))
    elements.append(Spacer(1, 12))

    _add_recent_updates(elements, updates, styles)
    elements.append(Spacer(1, 24))

    signature_data = [
        ["Teacher Signature", "Admin Signature"],
        ["", ""],
    ]
    signature_table = Table(signature_data, colWidths=[3.2 * inch, 3.2 * inch], rowHeights=[0.35 * inch, 0.55 * inch])
    signature_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 1), (0, 1), 1, colors.black),
        ("LINEBELOW", (1, 1), (1, 1), 1, colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#555555")),
    ]))
    elements.append(signature_table)

    doc.build(elements)
    return response

