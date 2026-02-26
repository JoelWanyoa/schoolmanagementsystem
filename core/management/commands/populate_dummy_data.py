# core/management/commands/populate_dummy_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from core.models import (
    SchoolInfo, AcademicYear, Class, Section, Subject, Student, Teacher, Parent,
    Fee, Expense, Book, BookBorrowing, TransportRoute, Vehicle, Hostel, HostelRoom,
    HostelAllocation, Attendance, Exam, ExamResult, Assignment, AssignmentSubmission,
    Notice, Message, Event, InventoryItem, GradingSystem, Staff, Reminder,
    Timetable, ClassSubject
)
from datetime import datetime, timedelta, date
import random
from decimal import Decimal, InvalidOperation
from faker import Faker
import string

fake = Faker()

class Command(BaseCommand):
    help = 'Populates the database with realistic dummy data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=50, help='Number of students to create')
        parser.add_argument('--teachers', type=int, default=15, help='Number of teachers to create')
        parser.add_argument('--parents', type=int, default=40, help='Number of parents to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing data first')
        parser.add_argument('--skip-existing', action='store_true', help='Skip if data exists')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('POPULATING DUMMY DATA FOR SCHOOL MANAGEMENT SYSTEM'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Clear existing data if requested
        if options['clear']:
            self.clear_existing_data()

        # Check if data already exists
        if options['skip_existing'] and Class.objects.exists():
            self.stdout.write(self.style.WARNING('Data already exists. Skipping...'))
            return

        try:
            # Create basic school structure
            self.create_school_info()
            self.create_academic_years()
            self.create_classes_and_sections()
            self.create_subjects()
            
            # Skip grading system for now - comment this out if causing issues
            # self.create_grading_system()
            self.stdout.write(self.style.WARNING('⚠️  Skipping grading system creation'))
            
            # Create users and profiles
            teachers = self.create_teachers(options['teachers'])
            parents = self.create_parents(options['parents'])
            students = self.create_students(options['students'], teachers, parents)
            
            # Create class-subject-teacher allocations
            self.create_class_subjects(teachers)
            
            # Create timetables
            self.create_timetables(teachers)
            
            # Create academic data
            self.create_attendance(students)
            self.create_exams()
            self.create_exam_results(students)
            self.create_assignments(students, teachers)
            
            # Create financial data
            self.create_fees(students)
            self.create_expenses()
            
            # Create library data
            self.create_books()
            self.create_book_borrowings(students)
            
            # Create transport data
            self.create_transport_routes()
            self.create_vehicles()
            
            # Create hostel data
            self.create_hostels()
            self.allocate_hostels(students)
            
            # Create communication data
            self.create_notices(teachers)
            self.create_messages(teachers, students, parents)
            self.create_events()
            
            # Create inventory
            self.create_inventory()
            
            # Create staff
            self.create_staff()
            
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('✅ DUMMY DATA POPULATION COMPLETED SUCCESSFULLY!'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
            # Summary
            self.print_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

    def clear_existing_data(self):
        """Clear all existing data from the database"""
        self.stdout.write('Clearing existing data...')
        
        # Delete in correct order to avoid foreign key issues
        models_to_delete = [
            Message, Notice, Event, Timetable, ClassSubject,
            AssignmentSubmission, Assignment, ExamResult, Exam,
            Attendance, Fee, Expense, Reminder,
            BookBorrowing, Book, InventoryItem,
            HostelAllocation, HostelRoom, Hostel,
            Vehicle, TransportRoute,
            Student, Teacher, Parent, Staff,
            Section, Class, Subject, AcademicYear,
            GradingSystem, SchoolInfo
        ]
        
        for model in models_to_delete:
            model.objects.all().delete()
        
        # Delete users (except superuser)
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS('✅ Existing data cleared'))

    def create_school_info(self):
        """Create school information"""
        if SchoolInfo.objects.exists():
            self.stdout.write('School info already exists')
            return
        
        school = SchoolInfo.objects.create(
            name="Petra School of Excellence",
            address="123 Education Avenue, Nairobi, Kenya",
            phone="+254 700 123456",
            email="info@petra.edu",
            established_date=date(2005, 1, 15)
        )
        self.stdout.write(f'✅ Created school: {school.name}')

    def create_academic_years(self):
        """Create academic years"""
        current_year = datetime.now().year
        
        academic_years = [
            {
                'name': f'{current_year-2}-{current_year-1}',
                'start_date': date(current_year-2, 1, 10),
                'end_date': date(current_year-1, 11, 30),
                'is_current': False
            },
            {
                'name': f'{current_year-1}-{current_year}',
                'start_date': date(current_year-1, 1, 10),
                'end_date': date(current_year, 11, 30),
                'is_current': True
            },
            {
                'name': f'{current_year}-{current_year+1}',
                'start_date': date(current_year, 1, 10),
                'end_date': date(current_year+1, 11, 30),
                'is_current': False
            }
        ]
        
        for year_data in academic_years:
            AcademicYear.objects.get_or_create(
                name=year_data['name'],
                defaults=year_data
            )
        
        self.stdout.write('✅ Created academic years')

    def create_classes_and_sections(self):
        """Create classes and sections"""
        classes_data = [
            # ECDE
            {'level_category': 'ECDE', 'grade_level': 'PP1', 'capacity': 30},
            {'level_category': 'ECDE', 'grade_level': 'PP2', 'capacity': 30},
            
            # Primary
            {'level_category': 'PRIMARY', 'grade_level': '1', 'capacity': 40},
            {'level_category': 'PRIMARY', 'grade_level': '2', 'capacity': 40},
            {'level_category': 'PRIMARY', 'grade_level': '3', 'capacity': 40},
            {'level_category': 'PRIMARY', 'grade_level': '4', 'capacity': 40},
            {'level_category': 'PRIMARY', 'grade_level': '5', 'capacity': 40},
            {'level_category': 'PRIMARY', 'grade_level': '6', 'capacity': 40},
            
            # Junior Secondary
            {'level_category': 'JUNIOR_SECONDARY', 'grade_level': '7', 'capacity': 35},
            {'level_category': 'JUNIOR_SECONDARY', 'grade_level': '8', 'capacity': 35},
            {'level_category': 'JUNIOR_SECONDARY', 'grade_level': '9', 'capacity': 35},
        ]
        
        sections = ['A', 'B', 'C']
        
        for class_data in classes_data:
            class_obj, created = Class.objects.get_or_create(
                grade_level=class_data['grade_level'],
                level_category=class_data['level_category'],
                defaults={
                    'capacity': class_data['capacity'],
                    'code': f"{class_data['level_category']}_{class_data['grade_level']}"
                }
            )
            
            # Create sections for each class
            for section_name in sections:
                Section.objects.get_or_create(
                    name=section_name,
                    class_name=class_obj,
                    defaults={
                        'capacity': class_data['capacity'] // len(sections),
                        'room_number': f"{class_obj.grade_level}-{section_name}"
                    }
                )
        
        self.stdout.write('✅ Created classes and sections')

    def create_subjects(self):
        """Create subjects"""
        subjects_data = [
            # Core Subjects
            {'name': 'Mathematics', 'code': 'MATH01', 'category': 'CORE', 'credit_hours': 5},
            {'name': 'English', 'code': 'ENG01', 'category': 'CORE', 'credit_hours': 5},
            {'name': 'Kiswahili', 'code': 'KIS01', 'category': 'CORE', 'credit_hours': 5},
            {'name': 'Science', 'code': 'SCI01', 'category': 'CORE', 'credit_hours': 4},
            {'name': 'Social Studies', 'code': 'SST01', 'category': 'CORE', 'credit_hours': 3},
            {'name': 'Religious Education', 'code': 'RE01', 'category': 'CORE', 'credit_hours': 2},
            
            # Primary Electives
            {'name': 'Agriculture', 'code': 'AGR01', 'category': 'ELECTIVE', 'credit_hours': 2},
            {'name': 'Home Science', 'code': 'HSC01', 'category': 'ELECTIVE', 'credit_hours': 2},
            {'name': 'Art & Craft', 'code': 'ART01', 'category': 'ELECTIVE', 'credit_hours': 2},
            {'name': 'Music', 'code': 'MUS01', 'category': 'ELECTIVE', 'credit_hours': 2},
            {'name': 'Physical Education', 'code': 'PE01', 'category': 'ELECTIVE', 'credit_hours': 2},
            
            # Junior Secondary
            {'name': 'Physics', 'code': 'PHY01', 'category': 'CORE', 'credit_hours': 4},
            {'name': 'Chemistry', 'code': 'CHEM01', 'category': 'CORE', 'credit_hours': 4},
            {'name': 'Biology', 'code': 'BIO01', 'category': 'CORE', 'credit_hours': 4},
            {'name': 'History', 'code': 'HIS01', 'category': 'CORE', 'credit_hours': 3},
            {'name': 'Geography', 'code': 'GEO01', 'category': 'CORE', 'credit_hours': 3},
            {'name': 'Business Studies', 'code': 'BUS01', 'category': 'ELECTIVE', 'credit_hours': 3},
            {'name': 'Computer Science', 'code': 'COM01', 'category': 'ELECTIVE', 'credit_hours': 3},
            {'name': 'French', 'code': 'FR01', 'category': 'OPTIONAL', 'credit_hours': 2},
            {'name': 'German', 'code': 'GER01', 'category': 'OPTIONAL', 'credit_hours': 2},
        ]
        
        for subject_data in subjects_data:
            Subject.objects.get_or_create(
                code=subject_data['code'],
                defaults=subject_data
            )
        
        self.stdout.write('✅ Created subjects')

    # core/management/commands/populate_dummy_data.py

    def create_teachers(self, count):
        """Create teachers with guaranteed unique teacher IDs"""
        teachers = []
        subjects = list(Subject.objects.all())
        genders = ['M', 'F']
        teaching_levels = ['ECDE', 'PRIMARY', 'JUNIOR_SECONDARY', 'ALL']
        
        self.stdout.write(f'Creating {count} teachers...')
        
        # Get the highest existing teacher ID number to start from
        existing_teachers = Teacher.objects.all().order_by('-id')
        start_id = 1
        if existing_teachers.exists():
            # Try to extract the numeric part from the last teacher_id
            last_teacher = existing_teachers.first()
            try:
                last_id_parts = last_teacher.teacher_id.split('-')
                if len(last_id_parts) >= 3:
                    start_id = int(last_id_parts[-1]) + 1
            except (ValueError, IndexError):
                # If can't parse, just use count + 1
                start_id = Teacher.objects.count() + 1
        
        created_count = 0
        for i in range(count):
            # Generate unique username
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Create base username
            base_username = f"{first_name.lower()}.{last_name.lower()}"
            username = base_username
            username_counter = 1
            
            # Ensure username is unique
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{username_counter}"
                username_counter += 1
            
            email = f"{username}@petra.edu"
            
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    password='password123',
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Add to Teacher group
                teacher_group, _ = Group.objects.get_or_create(name='Teacher')
                user.groups.add(teacher_group)
                
                # Generate unique teacher_id
                year = timezone.now().year
                teacher_id = f"TCH-{year}-{start_id + i:04d}"
                
                # Double-check that teacher_id doesn't already exist
                while Teacher.objects.filter(teacher_id=teacher_id).exists():
                    start_id += 1
                    teacher_id = f"TCH-{year}-{start_id + i:04d}"
                
                # Create teacher profile
                gender = random.choice(genders)
                teacher = Teacher.objects.create(
                    user=user,
                    teacher_id=teacher_id,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=60),
                    religion=random.choice(['Christian', 'Muslim', 'Hindu', 'Other']),
                    address=fake.address(),
                    phone=fake.phone_number()[:15],
                    email=email,
                    qualification=random.choice(['Bachelor', 'Master', 'PhD', 'Diploma']),
                    specialization=random.choice(['Mathematics', 'Science', 'Languages', 'Humanities']),
                    experience=random.randint(1, 30),
                    joining_date=fake.date_between(start_date='-10y', end_date='today'),
                    salary=random.randint(30000, 100000),
                    teaching_level=random.choice(teaching_levels),
                    is_active=True,
                    is_online=random.choice([True, False]),
                    last_activity=timezone.now() - timedelta(hours=random.randint(0, 24))
                )
                
                # Assign random subjects
                if subjects:
                    num_subjects = min(random.randint(2, 5), len(subjects))
                    assigned_subjects = random.sample(subjects, num_subjects)
                    teacher.subjects.set(assigned_subjects)
                
                teachers.append(teacher)
                created_count += 1
                
                if created_count % 5 == 0:
                    self.stdout.write(f'  Created {created_count} teachers')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating teacher {first_name} {last_name}: {str(e)}'))
                # Clean up user if teacher creation failed
                if 'user' in locals():
                    user.delete()
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(teachers)} teachers'))
        return teachers

    def create_parents(self, count):
        """Create parents"""
        parents = []
        
        self.stdout.write(f'Creating {count} parents...')
        
        for i in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"parent.{first_name.lower()}{random.randint(1,99)}"
            # Ensure username is unique
            while User.objects.filter(username=username).exists():
                username = f"parent.{first_name.lower()}{random.randint(100,999)}"
            
            email = f"{username}@example.com"
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password='password123',
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            
            # Add to Parent group
            parent_group, _ = Group.objects.get_or_create(name='Parent')
            user.groups.add(parent_group)
            
            # Create parent profile
            parent = Parent.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone=fake.phone_number()[:15],
                email=email,
                address=fake.address(),
                occupation=fake.job(),
                father_name=fake.name_male() if random.random() > 0.5 else '',
                mother_name=fake.name_female() if random.random() > 0.5 else '',
                is_online=random.choice([True, False]),
                last_activity=timezone.now() - timedelta(hours=random.randint(0, 48))
            )
            
            parents.append(parent)
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'  Created {i + 1} parents')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(parents)} parents'))
        return parents

    def create_students(self, count, teachers, parents):
        """Create students with guaranteed unique student IDs"""
        students = []
        classes = list(Class.objects.all())
        sections = list(Section.objects.all())
        genders = ['M', 'F']
        
        self.stdout.write(f'Creating {count} students...')
        
        # Assign class teachers
        for i, class_obj in enumerate(classes):
            if i < len(teachers):
                class_obj.class_teacher = teachers[i]
                class_obj.save()
        
        # Get the highest existing student ID number to start from
        existing_students = Student.objects.all().order_by('-id')
        start_id = 1
        if existing_students.exists():
            last_student = existing_students.first()
            try:
                last_id_parts = last_student.student_id.split('-')
                if len(last_id_parts) >= 3:
                    start_id = int(last_id_parts[-1]) + 1
            except (ValueError, IndexError):
                start_id = Student.objects.count() + 1
        
        created_count = 0
        for i in range(count):
            # Generate unique username
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            base_username = f"{first_name.lower()}.{last_name.lower()}"
            username = base_username
            username_counter = 1
            
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{username_counter}"
                username_counter += 1
            
            email = f"{username}@student.petra.edu"
            
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    password='student123',
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Add to Student group
                student_group, _ = Group.objects.get_or_create(name='Student')
                user.groups.add(student_group)
                
                # Assign class and section
                class_obj = random.choice(classes)
                section = random.choice([s for s in sections if s.class_name == class_obj])
                
                # Generate unique student_id
                year = timezone.now().year
                student_id = f"STU-{year}-{start_id + i:04d}"
                
                # Double-check that student_id doesn't already exist
                while Student.objects.filter(student_id=student_id).exists():
                    start_id += 1
                    student_id = f"STU-{year}-{start_id + i:04d}"
                
                # Create student profile
                gender = random.choice(genders)
                student = Student.objects.create(
                    user=user,
                    student_id=student_id,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    date_of_birth=fake.date_of_birth(minimum_age=5, maximum_age=18),
                    religion=random.choice(['Christian', 'Muslim', 'Hindu', 'Buddhist', 'Other']),
                    address=fake.address(),
                    phone=fake.phone_number()[:15],
                    email=email,
                    current_class=class_obj,
                    current_section=section,
                    roll_number=f"{class_obj.grade_level}{start_id + i:03d}",
                    admission_date=fake.date_between(start_date='-3y', end_date='today'),
                    # Parent information
                    father_name=fake.name_male(),
                    father_occupation=random.choice(['Engineer', 'Doctor', 'Teacher', 'Business', 'Farmer']),
                    father_phone=fake.phone_number()[:15],
                    mother_name=fake.name_female(),
                    mother_occupation=random.choice(['Nurse', 'Teacher', 'Accountant', 'Housewife', 'Business']),
                    mother_phone=fake.phone_number()[:15],
                    guardian_email=email.replace('student', 'parent'),
                    guardian_phone=fake.phone_number()[:15],
                    emergency_contact_name=fake.name(),
                    emergency_contact_phone=fake.phone_number()[:15],
                    emergency_relationship=random.choice(['Father', 'Mother', 'Uncle', 'Aunt', 'Guardian']),
                    previous_school=fake.company() + " School" if random.random() > 0.3 else '',
                    transfer_certificate_no=fake.bothify(text='TR-####-????') if random.random() > 0.5 else '',
                    medical_conditions=random.choice(['', 'Asthma', 'Allergies', 'None']),
                    medications=random.choice(['', 'Inhaler', 'Antihistamines', 'None']),
                    doctor_name=fake.name(),
                    doctor_phone=fake.phone_number()[:15],
                    national_id=fake.bothify(text='########'),
                    is_active=True,
                    is_online=random.choice([True, False]),
                    last_activity=timezone.now() - timedelta(hours=random.randint(0, 24))
                )
                
                # Assign to random parents
                if parents:
                    num_parents = min(random.randint(1, 2), len(parents))
                    student_parents = random.sample(parents, num_parents)
                    for parent in student_parents:
                        parent.students.add(student)
                
                students.append(student)
                created_count += 1
                
                if created_count % 10 == 0:
                    self.stdout.write(f'  Created {created_count} students')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating student {first_name} {last_name}: {str(e)}'))
                # Clean up user if student creation failed
                if 'user' in locals():
                    user.delete()
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(students)} students'))
        return students

    def create_class_subjects(self, teachers):
        """Create class subject allocations"""
        classes = Class.objects.all()
        subjects = list(Subject.objects.all())
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        if not academic_year:
            academic_year = AcademicYear.objects.first()
        
        for class_obj in classes:
            sections = Section.objects.filter(class_name=class_obj)
            
            for section in sections:
                # Assign 5-8 subjects per class section
                if subjects:
                    class_subjects = random.sample(subjects, min(random.randint(5, 8), len(subjects)))
                    
                    for subject in class_subjects:
                        teacher = random.choice(teachers) if teachers else None
                        
                        ClassSubject.objects.get_or_create(
                            class_level=class_obj,
                            section=section,
                            subject=subject,
                            academic_year=academic_year,
                            defaults={
                                'teacher': teacher,
                                'weekly_periods': random.randint(3, 6),
                                'is_compulsory': random.choice([True, True, True, False])  # 75% compulsory
                            }
                        )
        
        self.stdout.write('✅ Created class-subject allocations')

    def create_timetables(self, teachers):
        """Create timetables"""
        days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
        periods = [
            {'number': 1, 'start': '08:00', 'end': '08:40'},
            {'number': 2, 'start': '08:40', 'end': '09:20'},
            {'number': 3, 'start': '09:20', 'end': '10:00'},
            {'number': 4, 'start': '10:20', 'end': '11:00'},
            {'number': 5, 'start': '11:00', 'end': '11:40'},
            {'number': 6, 'start': '11:40', 'end': '12:20'},
            {'number': 7, 'start': '13:00', 'end': '13:40'},
            {'number': 8, 'start': '13:40', 'end': '14:20'},
        ]
        
        classes = Class.objects.all()
        
        for class_obj in classes:
            sections = Section.objects.filter(class_name=class_obj)
            class_subjects = ClassSubject.objects.filter(class_level=class_obj)
            
            for section in sections:
                section_subjects = [cs.subject for cs in class_subjects.filter(section=section)]
                
                for day in days:
                    # Create 5-7 periods per day
                    day_periods = random.sample(periods, random.randint(5, 7))
                    
                    for period in day_periods:
                        if section_subjects and random.random() > 0.2:  # 80% chance of subject period
                            subject = random.choice(section_subjects)
                            teacher = random.choice(teachers) if teachers else None
                            
                            Timetable.objects.create(
                                class_level=class_obj,
                                section=section,
                                subject=subject,
                                teacher=teacher,
                                day=day,
                                period_number=period['number'],
                                start_time=datetime.strptime(period['start'], '%H:%M').time(),
                                end_time=datetime.strptime(period['end'], '%H:%M').time(),
                                room=f"Room {random.randint(101, 305)}",
                                is_break=False
                            )
                        else:
                            # Break period
                            Timetable.objects.create(
                                class_level=class_obj,
                                section=section,
                                day=day,
                                period_number=period['number'],
                                start_time=datetime.strptime(period['start'], '%H:%M').time(),
                                end_time=datetime.strptime(period['end'], '%H:%M').time(),
                                is_break=True,
                                break_name=random.choice(['Break', 'Lunch Break', 'Short Break'])
                            )
        
        self.stdout.write('✅ Created timetables')

    def create_attendance(self, students):
        """Create attendance records"""
        attendance_count = 0
        today = timezone.now().date()
        
        for student in students:
            # Create attendance for the last 30 days
            for days_ago in range(1, 31):
                date = today - timedelta(days=days_ago)
                if date.weekday() < 5:  # Only weekdays
                    status = random.random() > 0.1  # 90% attendance rate
                    
                    Attendance.objects.create(
                        student=student,
                        date=date,
                        status=status,
                        remarks='' if status else random.choice(['Sick', 'Family event', 'Late']),
                        created_at=datetime.combine(date, datetime.min.time())
                    )
                    attendance_count += 1
        
        self.stdout.write(f'✅ Created {attendance_count} attendance records')

    def create_exams(self):
        """Create exams"""
        exam_count = 0
        exam_types = ['MIDTERM', 'FINAL', 'QUIZ', 'ASSIGNMENT', 'PROJECT']
        subjects = Subject.objects.all()
        classes = Class.objects.all()
        users = User.objects.filter(is_superuser=False).first()
        
        if not users:
            users = User.objects.first()
        
        for class_obj in classes:
            for exam_type in exam_types:
                for i in range(random.randint(2, 4)):  # 2-4 exams per type per class
                    subject = random.choice(subjects) if subjects else None
                    
                    if subject:
                        exam = Exam.objects.create(
                            name=f"{exam_type} {i+1} - {subject.name}",
                            exam_type=exam_type,
                            description=fake.text(max_nb_chars=200),
                            subject=subject,
                            class_level=class_obj,
                            exam_date=fake.date_between(start_date='-1m', end_date='+1m'),
                            start_time=datetime.strptime(f"{random.randint(8, 15)}:00", '%H:%M').time(),
                            end_time=datetime.strptime(f"{random.randint(9, 16)}:00", '%H:%M').time(),
                            duration=random.randint(60, 180),
                            room=f"Room {random.randint(101, 305)}",
                            total_marks=random.choice([50, 100, 100, 100, 150]),
                            passing_marks=random.choice([20, 40, 50, 60, 75]),
                            status=random.choice(['UPCOMING', 'ONGOING', 'COMPLETED']),
                            created_by=users
                        )
                        exam_count += 1
        
        self.stdout.write(f'✅ Created {exam_count} exams')

    def create_exam_results(self, students):
        """Create exam results"""
        results_count = 0
        exams = Exam.objects.all()
        
        for exam in exams:
            for student in students[:random.randint(10, len(students))]:  # Not all students take all exams
                if random.random() > 0.3:  # 70% of students have results
                    marks = random.randint(0, int(exam.total_marks))
                    
                    result = ExamResult.objects.create(
                        exam=exam,
                        student=student,
                        marks_obtained=marks,
                        remarks=''
                    )
                    results_count += 1
        
        self.stdout.write(f'✅ Created {results_count} exam results')

    def create_assignments(self, students, teachers):
        """Create assignments and submissions"""
        assignment_count = 0
        submission_count = 0
        
        assignment_types = ['HOMEWORK', 'PROJECT', 'QUIZ', 'ESSAY', 'PRESENTATION']
        classes = Class.objects.all()
        
        for class_obj in classes:
            subjects = ClassSubject.objects.filter(class_level=class_obj)
            
            for class_subject in subjects[:3]:  # 3 assignments per class
                teacher = random.choice(teachers) if teachers else None
                
                if teacher:
                    assignment = Assignment.objects.create(
                        title=f"{class_subject.subject.name} {random.choice(['Homework', 'Project', 'Assignment'])} #{random.randint(1, 5)}",
                        description=fake.text(max_nb_chars=300),
                        subject=class_subject.subject,
                        class_level=class_obj,
                        teacher=teacher,
                        assignment_type=random.choice(assignment_types),
                        total_marks=random.choice([20, 50, 100]),
                        due_date=timezone.now() + timedelta(days=random.randint(1, 14)),
                        status=random.choice(['DRAFT', 'PUBLISHED', 'CLOSED'])
                    )
                    assignment_count += 1
                    
                    # Create submissions for some students
                    class_students = [s for s in students if s.current_class == class_obj]
                    for student in class_students[:random.randint(5, len(class_students))]:
                        if random.random() > 0.2:  # 80% submission rate
                            submitted = random.random() > 0.3  # 70% actually submitted
                            
                            if submitted:
                                submitted_date = timezone.now() - timedelta(days=random.randint(0, 5))
                                marks = random.randint(0, int(assignment.total_marks)) if submitted else None
                                
                                AssignmentSubmission.objects.create(
                                    assignment=assignment,
                                    student=student,
                                    submission_text=fake.text(max_nb_chars=200),
                                    submitted_at=submitted_date,
                                    marks_obtained=marks,
                                    feedback=fake.sentence() if marks else '',
                                    submitted=submitted
                                )
                                submission_count += 1
        
        self.stdout.write(f'✅ Created {assignment_count} assignments and {submission_count} submissions')

    def create_fees(self, students):
        """Create fee records"""
        fee_count = 0
        fee_types = ['tuition', 'exam', 'transport', 'hostel', 'library', 'sports', 'activity', 'lab']
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        for student in students[:30]:  # Only for some students
            for fee_type in random.sample(fee_types, random.randint(3, 6)):
                amount = random.choice([5000, 10000, 15000, 20000, 25000, 30000])
                due_date = fake.date_between(start_date='-2m', end_date='+2m')
                
                fee = Fee.objects.create(
                    student=student if random.random() > 0.3 else None,
                    class_level=student.current_class,
                    academic_year=academic_year,
                    name=f"{dict(Fee.FEE_TYPES)[fee_type]} - {academic_year.name}",
                    fee_type=fee_type,
                    amount=amount,
                    status=random.choice(['paid', 'unpaid', 'unpaid', 'paid']),
                    due_date=due_date,
                    paid_date=due_date - timedelta(days=random.randint(1, 10)) if random.random() > 0.5 else None,
                    description=fake.sentence(),
                    created_by=User.objects.first()
                )
                fee_count += 1
        
        self.stdout.write(f'✅ Created {fee_count} fee records')

    def create_expenses(self):
        """Create expense records"""
        expense_count = 0
        expense_types = ['salary', 'transport', 'maintenance', 'purchase', 'utilities', 'other']
        
        for _ in range(50):
            expense = Expense.objects.create(
                name=fake.catch_phrase(),
                expense_type=random.choice(expense_types),
                amount=random.randint(1000, 500000),
                phone=fake.phone_number()[:15] if random.random() > 0.5 else '',
                email=fake.email() if random.random() > 0.5 else '',
                status=random.choice(['pending', 'paid', 'due', 'others']),
                date=fake.date_between(start_date='-1y', end_date='today'),
                description=fake.text(max_nb_chars=200),
                created_by=User.objects.first()
            )
            expense_count += 1
        
        self.stdout.write(f'✅ Created {expense_count} expense records')

    def create_books(self):
        """Create library books"""
        book_count = 0
        categories = ['TEXTBOOK', 'REFERENCE', 'STORY', 'SCIENCE', 'MATHEMATICS', 'LANGUAGE', 'HISTORY', 'GEOGRAPHY', 'OTHER']
        
        for i in range(100):
            title = fake.catch_phrase()
            author = fake.name()
            isbn = fake.isbn13()
            
            total_copies = random.randint(1, 20)
            available = random.randint(0, total_copies)
            
            book = Book.objects.create(
                title=title,
                author=author,
                isbn=isbn,
                category=random.choice(categories),
                publisher=fake.company(),
                published_date=fake.date_between(start_date='-20y', end_date='-1y'),
                total_copies=total_copies,
                available_copies=available,
                description=fake.text(max_nb_chars=200),
                location=f"Section {random.choice(['A', 'B', 'C'])} - Shelf {random.randint(1, 20)}",
                status='AVAILABLE' if available > 0 else 'BORROWED'
            )
            book_count += 1
        
        self.stdout.write(f'✅ Created {book_count} books')

    def create_book_borrowings(self, students):
        """Create book borrowing records"""
        borrow_count = 0
        books = Book.objects.all()
        
        for student in students[:40]:  # Only for some students
            for _ in range(random.randint(0, 3)):
                if books:
                    book = random.choice(books)
                    if book.available_copies > 0:
                        borrowed_date = fake.date_between(start_date='-2m', end_date='-1w')
                        due_date = borrowed_date + timedelta(days=14)
                        
                        borrowing = BookBorrowing.objects.create(
                            book=book,
                            borrower=student.user,
                            borrowed_date=borrowed_date,
                            due_date=due_date,
                            status=random.choice(['BORROWED', 'RETURNED', 'OVERDUE']),
                            fine_amount=0,
                            remarks=''
                        )
                        
                        # Update book availability
                        book.available_copies -= 1
                        book.save()
                        
                        borrow_count += 1
        
        self.stdout.write(f'✅ Created {borrow_count} book borrowings')

    def create_transport_routes(self):
        """Create transport routes"""
        routes = [
            {'name': 'North Route', 'start': 'City Center', 'end': 'North Gate', 'distance': 15.5, 'fare': 2500},
            {'name': 'South Route', 'start': 'City Center', 'end': 'South Valley', 'distance': 18.2, 'fare': 2800},
            {'name': 'East Route', 'start': 'City Center', 'end': 'East Side', 'distance': 12.8, 'fare': 2200},
            {'name': 'West Route', 'start': 'City Center', 'end': 'West End', 'distance': 20.1, 'fare': 3200},
            {'name': 'Central Route', 'start': 'City Center', 'end': 'Downtown', 'distance': 8.5, 'fare': 1500},
        ]
        
        for route_data in routes:
            TransportRoute.objects.create(
                name=route_data['name'],
                description=f"Transport route serving {route_data['end']} area",
                start_point=route_data['start'],
                end_point=route_data['end'],
                distance=route_data['distance'],
                fare=route_data['fare'],
                is_active=True
            )
        
        self.stdout.write('✅ Created transport routes')

    def create_vehicles(self):
        """Create vehicles"""
        routes = TransportRoute.objects.all()
        vehicle_types = ['BUS', 'VAN', 'CAR']
        
        for i in range(10):
            route = random.choice(routes) if routes else None
            
            Vehicle.objects.create(
                vehicle_number=f"K{random.choice(['A', 'B', 'C', 'D'])}{random.randint(100, 999)}",
                model=random.choice(['Toyota Hiace', 'Nissan Civilian', 'Isuzu Bus', 'Mitsubishi Rosa']),
                capacity=random.choice([14, 26, 33, 45, 60]),
                vehicle_type=random.choice(vehicle_types),
                driver_name=fake.name(),
                driver_phone=fake.phone_number()[:15],
                insurance_expiry=fake.date_between(start_date='-30d', end_date='+1y'),
                status=random.choice(['ACTIVE', 'MAINTENANCE', 'INACTIVE']),
                route=route
            )
        
        self.stdout.write('✅ Created vehicles')

    def create_hostels(self):
        """Create hostels"""
        hostels = [
            {'name': 'Boys Hostel A', 'type': 'BOYS', 'rooms': 30},
            {'name': 'Boys Hostel B', 'type': 'BOYS', 'rooms': 25},
            {'name': 'Girls Hostel C', 'type': 'GIRLS', 'rooms': 30},
            {'name': 'Girls Hostel D', 'type': 'GIRLS', 'rooms': 25},
        ]
        
        room_types = ['SINGLE', 'DOUBLE', 'TRIPLE', 'DORMITORY']
        
        for hostel_data in hostels:
            hostel = Hostel.objects.create(
                name=hostel_data['name'],
                type=hostel_data['type'],
                address=fake.address(),
                warden_name=fake.name(),
                warden_phone=fake.phone_number()[:15],
                total_rooms=hostel_data['rooms'],
                available_rooms=hostel_data['rooms']
            )
            
            # Create rooms
            for i in range(1, hostel_data['rooms'] + 1):
                capacity = random.choice([1, 2, 3, 4, 6])
                HostelRoom.objects.create(
                    room_number=f"{i:03d}",
                    hostel=hostel,
                    capacity=capacity,
                    room_type=random.choice(room_types),
                    cost_per_student=random.randint(5000, 15000),
                    facilities=random.choice(['Study desk, bed', 'All furnished', 'Basic', 'Premium']),
                    status=random.choice(['AVAILABLE', 'OCCUPIED', 'MAINTENANCE'])
                )
        
        self.stdout.write('✅ Created hostels')

    def allocate_hostels(self, students):
        """Allocate hostel rooms to students"""
        allocation_count = 0
        hostels = Hostel.objects.all()
        
        # Allocate only to older students (Grade 7-9)
        eligible_students = [s for s in students if s.current_class and s.current_class.grade_level in ['7', '8', '9']]
        
        for student in eligible_students[:int(len(eligible_students) * 0.6)]:  # 60% of eligible
            hostel_type = 'BOYS' if student.gender == 'M' else 'GIRLS'
            hostels_of_type = hostels.filter(type=hostel_type)
            
            if hostels_of_type:
                hostel = random.choice(hostels_of_type)
                rooms = HostelRoom.objects.filter(hostel=hostel, status='AVAILABLE')
                
                if rooms.exists():
                    room = random.choice(rooms)
                    
                    HostelAllocation.objects.create(
                        student=student,
                        room=room,
                        allocated_date=fake.date_between(start_date='-6m', end_date='today'),
                        status='ACTIVE'
                    )
                    
                    # Update room status
                    if room.available_beds <= 0:
                        room.status = 'OCCUPIED'
                        room.save()
                    
                    allocation_count += 1
        
        self.stdout.write(f'✅ Created {allocation_count} hostel allocations')

    def create_notices(self, teachers):
        """Create notices"""
        notice_count = 0
        
        for _ in range(30):
            notice = Notice.objects.create(
                title=fake.sentence(nb_words=6),
                content=fake.text(max_nb_chars=500),
                priority=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                target_audience=random.choice(['ALL', 'TEACHERS', 'STUDENTS', 'PARENTS']),
                publish_date=fake.date_time_between(start_date='-2m', end_date='now'),
                expiry_date=fake.date_between(start_date='-1m', end_date='+2m'),
                posted_by=random.choice(teachers).user if teachers else User.objects.first(),
                is_active=random.random() > 0.2  # 80% active
            )
            notice_count += 1
        
        self.stdout.write(f'✅ Created {notice_count} notices')

    def create_messages(self, teachers, students, parents):
        """Create messages between users"""
        message_count = 0
        all_users = list(User.objects.all())
        
        for _ in range(100):
            sender = random.choice(all_users)
            receiver = random.choice([u for u in all_users if u != sender])
            
            Message.objects.create(
                sender=sender,
                receiver=receiver,
                subject=fake.sentence(nb_words=4),
                content=fake.text(max_nb_chars=300),
                sent_date=fake.date_time_between(start_date='-1m', end_date='now'),
                is_read=random.random() > 0.4  # 60% read
            )
            message_count += 1
        
        self.stdout.write(f'✅ Created {message_count} messages')

    def create_events(self):
        """Create events"""
        event_count = 0
        event_types = ['ACADEMIC', 'SPORTS', 'CULTURAL', 'HOLIDAY', 'MEETING', 'OTHER']
        
        for _ in range(20):
            start_date = fake.date_time_between(start_date='-2m', end_date='+3m')
            end_date = start_date + timedelta(hours=random.randint(1, 24))
            
            Event.objects.create(
                title=fake.sentence(nb_words=6),
                description=fake.text(max_nb_chars=300),
                start_date=start_date,
                end_date=end_date,
                event_type=random.choice(event_types),
                location=fake.city() + " " + fake.street_name(),
                target_audience=random.choice(['ALL', 'TEACHERS', 'STUDENTS', 'PARENTS']),
                is_active=True,
                created_by=User.objects.first()
            )
            event_count += 1
        
        self.stdout.write(f'✅ Created {event_count} events')

    def create_inventory(self):
        """Create inventory items"""
        item_count = 0
        categories = ['STATIONERY', 'FURNITURE', 'EQUIPMENT', 'LAB', 'SPORTS', 'OTHER']
        
        items = [
            {'name': 'Desks', 'category': 'FURNITURE', 'unit_price': 5000},
            {'name': 'Chairs', 'category': 'FURNITURE', 'unit_price': 2000},
            {'name': 'Whiteboards', 'category': 'EQUIPMENT', 'unit_price': 8000},
            {'name': 'Projectors', 'category': 'EQUIPMENT', 'unit_price': 45000},
            {'name': 'Exercise Books', 'category': 'STATIONERY', 'unit_price': 50},
            {'name': 'Pens', 'category': 'STATIONERY', 'unit_price': 10},
            {'name': 'Pencils', 'category': 'STATIONERY', 'unit_price': 8},
            {'name': 'Textbooks', 'category': 'LAB', 'unit_price': 500},
            {'name': 'Football', 'category': 'SPORTS', 'unit_price': 1500},
            {'name': 'Basketball', 'category': 'SPORTS', 'unit_price': 1800},
            {'name': 'Microscopes', 'category': 'LAB', 'unit_price': 25000},
            {'name': 'Beakers', 'category': 'LAB', 'unit_price': 300},
        ]
        
        for item_data in items:
            quantity = random.randint(50, 500)
            InventoryItem.objects.create(
                name=item_data['name'],
                category=item_data['category'],
                quantity=quantity,
                unit_price=item_data['unit_price'],
                minimum_stock=random.randint(10, 50),
                location=f"Store {random.choice(['A', 'B', 'C'])}",
                description=fake.sentence(),
                last_restocked=fake.date_between(start_date='-3m', end_date='today')
            )
            item_count += 1
        
        self.stdout.write(f'✅ Created {item_count} inventory items')

    def create_grading_system(self):
        """Create grading system"""
        grades = [
            {'grade': 'A', 'min': 80, 'max': 100, 'points': 12, 'remarks': 'Excellent'},
            {'grade': 'B', 'min': 70, 'max': 79, 'points': 10, 'remarks': 'Very Good'},
            {'grade': 'C', 'min': 60, 'max': 69, 'points': 8, 'remarks': 'Good'},
            {'grade': 'D', 'min': 50, 'max': 59, 'points': 6, 'remarks': 'Pass'},
            {'grade': 'E', 'min': 40, 'max': 49, 'points': 4, 'remarks': 'Fair'},
            {'grade': 'F', 'min': 0, 'max': 39, 'points': 2, 'remarks': 'Fail'},
        ]
        
        for grade_data in grades:
            GradingSystem.objects.get_or_create(
                grade=grade_data['grade'],
                min_mark=grade_data['min'],
                max_mark=grade_data['max'],
                defaults={
                    'name': f"Grade {grade_data['grade']}",
                    'points': grade_data['points'],
                    'remarks': grade_data['remarks'],
                    'is_active': True
                }
            )
        
        self.stdout.write('✅ Created grading system')

    def create_staff(self):
        """Create non-teaching staff"""
        staff_count = 0
        staff_types = ['ADMIN', 'SUPPORT', 'SECURITY', 'CLEANING', 'OTHER']
        
        for i in range(20):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"staff.{first_name.lower()}{last_name.lower()[:3]}{i}"
            # Ensure username is unique
            while User.objects.filter(username=username).exists():
                username = f"staff.{first_name.lower()}{last_name.lower()[:3]}{random.randint(100,999)}"
            
            email = f"{username}@petra.edu"
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password='staff123',
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            
            # Add to Staff group
            staff_group, _ = Group.objects.get_or_create(name='Staff')
            user.groups.add(staff_group)
            
            # Generate staff_id
            year = timezone.now().year
            staff_id = f"STF-{year}-{i+1:04d}"
            
            Staff.objects.create(
                user=user,
                staff_id=staff_id,
                first_name=first_name,
                last_name=last_name,
                staff_type=random.choice(staff_types),
                phone=fake.phone_number()[:15],
                email=email,
                address=fake.address(),
                joining_date=fake.date_between(start_date='-5y', end_date='today'),
                salary=random.randint(20000, 60000),
                is_active=True
            )
            staff_count += 1
        
        self.stdout.write(f'✅ Created {staff_count} staff members')

    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 DATA SUMMARY:'))
        self.stdout.write('=' * 60)
        
        models_to_count = [
            ('Classes', Class),
            ('Sections', Section),
            ('Subjects', Subject),
            ('Teachers', Teacher),
            ('Students', Student),
            ('Parents', Parent),
            ('Staff', Staff),
            ('Exams', Exam),
            ('Exam Results', ExamResult),
            ('Assignments', Assignment),
            ('Assignment Submissions', AssignmentSubmission),
            ('Attendance Records', Attendance),
            ('Fees', Fee),
            ('Expenses', Expense),
            ('Books', Book),
            ('Book Borrowings', BookBorrowing),
            ('Transport Routes', TransportRoute),
            ('Vehicles', Vehicle),
            ('Hostels', Hostel),
            ('Hostel Rooms', HostelRoom),
            ('Hostel Allocations', HostelAllocation),
            ('Notices', Notice),
            ('Messages', Message),
            ('Events', Event),
            ('Inventory Items', InventoryItem),
        ]
        
        for label, model in models_to_count:
            count = model.objects.count()
            self.stdout.write(f'  {label:<20}: {count:>5}')
        
        self.stdout.write('=' * 60)