# Generated for Teachers Portal V9

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0002_teachingschedule'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ScheduleEntry',
        ),
    ]
