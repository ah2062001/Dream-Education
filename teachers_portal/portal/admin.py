from django.contrib import admin

from .forms import TeachingScheduleAdminForm
from .models import ClassUpdate, Student, TeacherProfile, TeachingSchedule, TestScore


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user', 'subject_specialty', 'phone')
    search_fields = ('display_name', 'user__username', 'subject_specialty')


@admin.register(TeachingSchedule)
class TeachingScheduleAdmin(admin.ModelAdmin):
    form = TeachingScheduleAdminForm
    list_display = (
        'teacher', 'title', 'subject', 'student_name', 'classes_per_week', 'start_date', 'end_date', 'start_time', 'end_time'
    )
    list_filter = ('teacher', 'subject', 'start_date', 'end_date')
    search_fields = ('teacher__display_name', 'title', 'subject', 'student_name', 'student_details', 'notes')
    fieldsets = (
        ('Teacher & Student', {
            'fields': ('teacher', 'title', 'subject', 'student_name', 'student_details')
        }),
        ('Recurring Schedule', {
            'fields': ('weekdays', 'start_date', 'end_date', 'start_time', 'end_time', 'location')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from portal.utils.google_sync import sync_schedule_raw
            sync_schedule_raw()
        except Exception as e:
            print('Google Sheets schedule sync failed:', e)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        try:
            from portal.utils.google_sync import sync_schedule_raw
            sync_schedule_raw()
        except Exception as e:
            print('Google Sheets schedule sync failed:', e)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'student_type', 'teacher', 'school_name', 'year_group', 'guardian_name', 'created_at')
    list_filter = ('student_type', 'teacher', 'school_name', 'year_group')
    search_fields = ('full_name', 'preferred_name', 'guardian_name', 'guardian_contact')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from portal.utils.student_sync import sync_students_workbook
            sync_students_workbook()
        except Exception as e:
            print('Google Sheets student sync failed:', e)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        try:
            from portal.utils.student_sync import sync_students_workbook
            sync_students_workbook()
        except Exception as e:
            print('Google Sheets student sync failed:', e)


@admin.register(ClassUpdate)
class ClassUpdateAdmin(admin.ModelAdmin):
    list_display = ('student', 'update_type', 'lesson_date', 'title', 'class_marks', 'max_marks')
    list_filter = ('update_type', 'lesson_date', 'student__teacher')
    search_fields = ('student__full_name', 'title', 'work_done')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from portal.utils.student_sync import sync_students_workbook
            sync_students_workbook()
        except Exception as e:
            print('Google Sheets student sync failed:', e)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        try:
            from portal.utils.student_sync import sync_students_workbook
            sync_students_workbook()
        except Exception as e:
            print('Google Sheets student sync failed:', e)


@admin.register(TestScore)
class TestScoreAdmin(admin.ModelAdmin):
    list_display = ('student', 'period_type', 'assessment_name', 'score', 'total_marks', 'assessment_date')
    list_filter = ('period_type', 'assessment_date', 'student__teacher')
    search_fields = ('student__full_name', 'assessment_name', 'remarks')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from portal.utils.student_sync import sync_students_workbook
            sync_students_workbook()
        except Exception as e:
            print('Google Sheets student sync failed:', e)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        try:
            from portal.utils.student_sync import sync_students_workbook
            sync_students_workbook()
        except Exception as e:
            print('Google Sheets student sync failed:', e)
