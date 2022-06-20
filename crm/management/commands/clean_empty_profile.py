from django.core.management.base import BaseCommand
from crm.models import User


class Command(BaseCommand):
    help = 'Command delete user with empty profile'

    def handle(self, *args, **options):

        users = User.objects.all()
        # if user don't have profile - user delete.
        for user in users:
            try:
                user.profile
            except:
                user.delete()

        # self.stdout.write(tasks) # output message in console.

