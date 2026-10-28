from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('schedule/', views.schedule_calendar, name='schedule_calendar'),
    path('students/new/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/updates/new/', views.add_update, name='add_update'),
    path('students/<int:pk>/scores/new/', views.add_score, name='add_score'),
    path('students/<int:pk>/scores/<int:score_id>/edit/', views.edit_score, name='edit_score'),
    path('students/<int:pk>/report/', views.download_report, name='download_report'),
]
