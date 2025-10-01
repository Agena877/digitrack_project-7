from django.core.management.base import BaseCommand
from DigiTrackProject.tourism.models import Homestay, CustomUser

class Command(BaseCommand):
    help = 'Set the owner of a homestay to a specific user.'

    def add_arguments(self, parser):
        parser.add_argument('--homestay', type=str, required=True, help='Homestay name')
        parser.add_argument('--username', type=str, required=True, help='Username of the new owner')

    def handle(self, *args, **options):
        homestay_name = options['homestay']
        username = options['username']
        user = CustomUser.objects.filter(username=username).first()
        homestay = Homestay.objects.filter(name=homestay_name).first()
        if user and homestay:
            homestay.owner = user
            homestay.save()
            self.stdout.write(self.style.SUCCESS(f"Set owner of '{homestay_name}' to '{username}'"))
        else:
            self.stdout.write(self.style.ERROR('User or Homestay not found. Check names.'))
