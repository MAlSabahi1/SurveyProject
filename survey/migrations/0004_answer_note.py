# Generated by Django 5.1.3 on 2024-11-19 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_remove_answer_answer_data_answer_answer_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
    ]
