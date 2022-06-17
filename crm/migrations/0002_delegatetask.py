# Generated by Django 4.0.2 on 2022-06-16 12:54

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DelegateTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_executor', models.CharField(max_length=100)),
                ('new_executor', models.CharField(max_length=100)),
                ('date_delegate', models.DateField(default=datetime.date.today)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.task')),
            ],
        ),
    ]
