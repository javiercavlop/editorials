from django.core.management.base import BaseCommand
from ...populate import reset

class Command(BaseCommand):
    
    help = 'Reset the database deleting all the data'

    def handle(self, *args, **options):
        reset()