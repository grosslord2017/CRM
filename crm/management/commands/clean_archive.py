from django.core.management.base import BaseCommand
from crm.models import ArchiveTask, Task
from datetime import date

class Command(BaseCommand):
    help = 'Command checks for old entries in the archive and deletes'

    def handle(self, *args, **options):

        archive_tasks = ArchiveTask.objects.order_by('date_complete')
        day_now = date.today()
        for archive_task in archive_tasks:
            days = str(day_now - archive_task.date_complete).split() # format 731 days, 0:00:00
            if len(days) > 1:
                days = int(days[0])
                if days > 180:
                    archive_task.delete()
                    Task.objects.get(id=archive_task.task_id).delete()
                else:
                    continue

        # self.stdout.write(tasks) # output message in console.

