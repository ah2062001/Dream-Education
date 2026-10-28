# Generated for V10 clean student type feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0004_classupdate_marks'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='student_type',
            field=models.CharField(
                choices=[
                    ('math', 'Math'),
                    ('science', 'Science'),
                    ('english', 'English'),
                    ('ielts', 'IELTS'),
                ],
                default='english',
                max_length=20,
            ),
        ),
    ]
