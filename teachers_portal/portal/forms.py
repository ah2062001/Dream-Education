from django import forms
from .models import ClassUpdate, Student, TeachingSchedule, TestScore


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_type',
            'full_name',
            'preferred_name',
            'school_name',
            'year_group',
            'guardian_name',
            'guardian_contact',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ClassUpdateForm(forms.ModelForm):
    class Meta:
        model = ClassUpdate
        fields = ['update_type', 'lesson_date', 'title', 'work_done', 'homework', 'class_marks', 'max_marks', 'teacher_comment']
        widgets = {
            'lesson_date': forms.DateInput(attrs={'type': 'date'}),
            'work_done': forms.Textarea(attrs={'rows': 4}),
            'homework': forms.Textarea(attrs={'rows': 3}),
            'teacher_comment': forms.Textarea(attrs={'rows': 3}),
        }


class TestScoreForm(forms.ModelForm):
    class Meta:
        model = TestScore
        fields = ['period_type', 'assessment_name', 'score', 'total_marks', 'assessment_date', 'remarks']
        widgets = {
            'assessment_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TeachingScheduleAdminForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=TeachingSchedule.WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        help_text='Choose the teaching days. Two selected days means two classes per week.',
    )

    class Meta:
        model = TeachingSchedule
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['weekdays'].initial = self.instance.weekday_list

    def clean(self):
        cleaned = super().clean()
        weekdays = cleaned.get('weekdays') or []
        start_date = cleaned.get('start_date')
        end_date = cleaned.get('end_date')
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'End date must be on or after the start date.')
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'End time must be later than start time.')
        if not weekdays:
            self.add_error('weekdays', 'Select at least one teaching day.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.weekdays = ','.join(self.cleaned_data['weekdays'])
        if commit:
            instance.save()
        return instance
