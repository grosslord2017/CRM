from django.core.management.base import BaseCommand
from crm.models import VerifiCode
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Command removes codes that are older than 1 minute'

    def handle(self, *args, **options):

        codes = VerifiCode.objects.all()
        time_now = datetime.now().time()
        for code in codes:
            time_1 = datetime.strptime(str(code.time_create).split('.')[0], "%H:%M:%S")
            time_2 = datetime.strptime(str(time_now).split('.')[0], "%H:%M:%S")
            delta_time = time_2 - time_1
            if delta_time.seconds > 60:
                code.delete()
            else:
                continue




