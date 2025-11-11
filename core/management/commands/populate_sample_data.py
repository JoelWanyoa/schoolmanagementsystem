from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import *
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create Academic Year
        academic_year, created = AcademicYear.objects.get_or_create(
            name="2024-2025",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            is_current=True
        )
        
        # Create Classes
        classes_data = [
            {'name': 'Class 1', 'code': 'C1', 'capacity': 30},
            {'name': 'Class 2', 'code': 'C2', 'capacity': 30},
            {'name': 'Class 3', 'code': 'C3', 'capacity': 30},
        ]
        
        for class_data in classes_data:
            Class.objects.get_or_create(**class_data)
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))