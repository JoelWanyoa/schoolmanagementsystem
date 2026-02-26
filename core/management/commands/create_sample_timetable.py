from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Class, Section, Subject, Teacher, Timetable
from datetime import time

class Command(BaseCommand):
    help = 'Create sample timetable data'

    def handle(self, *args, **options):
        # Clear existing timetable
        Timetable.objects.all().delete()
        
        # Get sample data
        classes = Class.objects.all()
        if not classes.exists():
            self.stdout.write(self.style.ERROR('No classes found. Please create classes first.'))
            return
        
        sample_class = classes.first()
        sections = Section.objects.filter(class_name=sample_class)
        subjects = Subject.objects.all()[:6]  # Use first 6 subjects
        teachers = Teacher.objects.all()[:6]  # Use first 6 teachers
        
        if not sections.exists():
            self.stdout.write(self.style.ERROR('No sections found for the class.'))
            return
        
        sample_section = sections.first()
        
        # Define period times
        periods = [
            (1, time(8, 0), time(8, 40)),
            (2, time(8, 40), time(9, 20)),
            (3, time(9, 20), time(10, 0)),
            (4, time(10, 0), time(10, 20), True, 'Short Break'),  # Break
            (5, time(10, 20), time(11, 0)),
            (6, time(11, 0), time(11, 40)),
            (7, time(11, 40), time(12, 20)),
            (8, time(12, 20), time(13, 0), True, 'Lunch Break'),  # Break
            (9, time(13, 0), time(13, 40)),
            (10, time(13, 40), time(14, 20)),
        ]
        
        # Sample timetable structure
        timetable_data = {
            'MONDAY': ['Mathematics', 'English', 'Science', 'BREAK', 'Social Studies', 'CRE', 'Kiswahili', 'BREAK', 'Agriculture', 'Computer'],
            'TUESDAY': ['English', 'Mathematics', 'Social Studies', 'BREAK', 'Science', 'Kiswahili', 'CRE', 'BREAK', 'Physical Education', 'Music'],
            'WEDNESDAY': ['Science', 'Social Studies', 'Mathematics', 'BREAK', 'English', 'CRE', 'Kiswahili', 'BREAK', 'Art', 'Agriculture'],
            'THURSDAY': ['Social Studies', 'Science', 'English', 'BREAK', 'Mathematics', 'Kiswahili', 'CRE', 'BREAK', 'Computer', 'Physical Education'],
            'FRIDAY': ['Mathematics', 'English', 'Science', 'BREAK', 'Social Studies', 'Assembly', 'Kiswahili', 'BREAK', 'Music', 'Art'],
        }
        
        created_count = 0
        for day, subjects_list in timetable_data.items():
            for period_idx, subject_name in enumerate(subjects_list):
                period_info = periods[period_idx]
                period_num = period_info[0]
                start_time = period_info[1]
                end_time = period_info[2]
                is_break = period_info[3] if len(period_info) > 3 else False
                break_name = period_info[4] if len(period_info) > 4 else ''
                
                if subject_name == 'BREAK':
                    # Create break entry
                    timetable = Timetable.objects.create(
                        class_level=sample_class,
                        section=sample_section,
                        subject=None,  # No subject for breaks
                        teacher=None,  # No teacher for breaks
                        day=day,
                        period_number=period_num,
                        start_time=start_time,
                        end_time=end_time,
                        is_break=True,
                        break_name=break_name,
                    )
                else:
                    # Find subject and teacher
                    subject = subjects.filter(name=subject_name).first()
                    teacher = teachers[period_idx % len(teachers)] if teachers.exists() else None
                    
                    if subject and teacher:
                        timetable = Timetable.objects.create(
                            class_level=sample_class,
                            section=sample_section,
                            subject=subject,
                            teacher=teacher,
                            day=day,
                            period_number=period_num,
                            start_time=start_time,
                            end_time=end_time,
                            room=f"Room {100 + period_idx}",
                        )
                        created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} timetable entries for {sample_class.name} - Section {sample_section.name}'
            )
        )