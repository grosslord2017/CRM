from django.core.management.base import BaseCommand
from crm.models import ArchiveTask
from datetime import date

class Command(BaseCommand):
    help = 'Command checks for old entries in the archive and deletes'

    def handle(self, *args, **options):

        tasks = ArchiveTask.objects.order_by('date_complete')
        day_now = date.today()
        for task in tasks:
            days = str(day_now - task.date_complete).split()[0]
            if int(days) > 180:
                task.delete()
            else:
                continue
        # self.stdout.write(tasks) # output message in console.

