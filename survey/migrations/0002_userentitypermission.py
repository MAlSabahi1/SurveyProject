# Generated by Django 5.1.3 on 2024-11-28 05:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserEntityPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_permissions', to='survey.entitys')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_permissions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]