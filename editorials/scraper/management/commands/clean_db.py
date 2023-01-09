from django.core.management.base import BaseCommand
from ...populate import clean

class Command(BaseCommand):
    
    help = 'Deletes all the tables from the databse affected by the "populate_db" command'

    def handle(self, *args, **options):
        clean()