# Generated for Teachers Portal V9

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0003_delete_scheduleentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='classupdate',
            name='class_marks',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='classupdate',
            name='max_marks',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
