# core/migrations/0008_fix_fee_data.py
from django.db import migrations

def create_default_academic_years(apps, schema_editor):
    AcademicYear = apps.get_model('core', 'AcademicYear')
    
    # Create default academic years if they don't exist
    default_years = [
        {'name': '2023-2024', 'start_date': '2023-09-01', 'end_date': '2024-08-31', 'is_current': False},
        {'name': '2024-2025', 'start_date': '2024-09-01', 'end_date': '2025-08-31', 'is_current': True},
        {'name': '2025-2026', 'start_date': '2025-09-01', 'end_date': '2026-08-31', 'is_current': False},
    ]
    
    for year_data in default_years:
        AcademicYear.objects.get_or_create(
            name=year_data['name'],
            defaults=year_data
        )

def fix_fee_academic_years(apps, schema_editor):
    Fee = apps.get_model('core', 'Fee')
    AcademicYear = apps.get_model('core', 'AcademicYear')
    
    # Get or create the current academic year
    current_year, created = AcademicYear.objects.get_or_create(
        name='2024-2025',
        defaults={
            'start_date': '2024-09-01',
            'end_date': '2025-08-31',
            'is_current': True
        }
    )
    
    # Update all fees to use the current academic year
    Fee.objects.filter(academic_year__isnull=True).update(academic_year=current_year)

def reverse_migration(apps, schema_editor):
    # This is the reverse function - we don't need to do anything specific
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_class_options_alter_section_options_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_academic_years, reverse_migration),
        migrations.RunPython(fix_fee_academic_years, reverse_migration),
    ]