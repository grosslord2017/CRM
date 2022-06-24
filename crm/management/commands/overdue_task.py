from django.core.management.base import BaseCommand
from crm.models import Task
from crm.sender import send_mail
from datetime import date
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'The command to send a message to the director if the task is overdue'

    def handle(self, *args, **options):
        tasks = Task.objects.all()
        date_now = date.today()
        for task in tasks:
            if task.final_date < date_now:
                reporter = User.objects.get(id=task.task_manager_id).email
                subject = f'Overdue task: {task.subject}'
                body = f"System info: " \
                       f"\n\n Task {task.subject} is overdue!!!" \
                       f"\n\n please complete the task."
                send_mail(reporter, subject, body)

