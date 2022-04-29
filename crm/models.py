from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    # category_fk = models.ForeignKey('Category', on_delete=models.CASCADE, default=None, null=True)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    name = models.CharField(max_length=50, default='')
    surname = models.CharField(max_length=100, default='')
    patronymic = models.CharField(max_length=50, default='')
    telephone = models.CharField(max_length=20, default='')
    department = models.CharField(max_length=200, default='')
    position = models.CharField(max_length=200, default='')


class Task(models.Model):

    subject = models.CharField(max_length=150)
    date_create = models.DateField(default=date.today)
    final_date = models.DateField()
    description = models.CharField(max_length=1000)
    status_completed = models.BooleanField(default=False)
    task_manager = models.ForeignKey(User, on_delete=models.CASCADE)
    executor = models.ForeignKey(Profile, on_delete=models.CASCADE, default=None)


class Coment(models.Model):

    task_fk = models.ForeignKey(Task, on_delete=models.CASCADE, default=None, null=True)
    text = models.CharField(max_length=5000)
    date = models.DateTimeField(default=timezone.now)

# class HistoryTask(models.Model):
#
#     who = models.ForeignKey(User, on_delete=models.CASCADE)
#     whom = models.ForeignKey(Profile, on_delete=models.CASCADE)
#     task = models.ForeignKey(Task, on_delete=models.CASCADE)
#
class ArchiveTask(models.Model):

    date_create = models.DateField()
    date_complite = models.DateField(default=date.today)
    subject = models.CharField(max_length=150)
    task_manager = models.CharField(max_length=150)
    executor = models.CharField(max_length=150)
    description = models.CharField(max_length=1000)






