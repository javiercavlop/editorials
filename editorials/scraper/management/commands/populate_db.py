from django.core.management.base import BaseCommand
from ...populate import populate

class Command(BaseCommand):
    
    help = 'Populates some of the tables of the database with some initial data'

    def handle(self, *args, **options):
        populate()
    