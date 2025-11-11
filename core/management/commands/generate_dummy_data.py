# core/management/commands/generate_dummy_data.py
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from core.models import *

class Command(BaseCommand):
    help = 'Generate comprehensive dummy data for the school management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before generating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing all existing data...')
            self.clear_data()
        
        self.stdout.write('Generating dummy data...')
        
        # Create groups
        self.create_groups()
        
        # Create academic years
        academic_years = self.create_academic_years()
        
        # Create classes and sections
        classes = self.create_classes()
        sections = self.create_sections(classes)
        
        # Create subjects
        subjects = self.create_subjects()
        
        # Create school info
        self.create_school_info()
        
        # Create admin user
        self.create_admin_user()
        
        # Create teachers
        teachers = self.create_teachers(subjects)
        
        # Assign class teachers
        self.assign_class_teachers(classes, teachers)
        
        # Create parents and students with proper relationships
        parents, students = self.create_parents_and_students(classes, sections)
        
        # Create attendance records
        self.create_attendance(students)
        
        # Create exams and results
        self.create_exams_and_results(classes, subjects, students)
        
        # Create fees and payments
        self.create_fees_and_payments(students, academic_years[1])  # Use current academic year
        
        # Create expenses
        self.create_expenses()
        
        # Create notices
        self.create_notices()
        
        # Create messages
        self.create_messages()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated dummy data:\n'
                f'- {len(teachers)} teachers\n'
                f'- {len(parents)} parents\n'
                f'- {len(students)} students\n'
                f'- {len(classes)} classes\n'
                f'- {len(subjects)} subjects\n'
                f'- {len(sections)} sections\n'
                f'- Various attendance, exam, fee, and expense records'
            )
        )

    def clear_data(self):
        """Clear all existing data"""
        # Clear in reverse order to handle foreign key constraints
        models = [
            FeePayment, Fee, Expense, ExamResult, Exam, Attendance,
            AdmissionForm, Message, Notice, 
            Student, Parent, Teacher,
            Section, Class, Subject, AcademicYear, SchoolInfo
        ]
        
        for model in models:
            count = model.objects.count()
            model.objects.all().delete()
            if count > 0:
                self.stdout.write(f'✓ Deleted {count} {model.__name__} records')
        
        # Delete custom users but keep admin
        user_count = User.objects.exclude(username='admin').count()
        User.objects.exclude(username='admin').delete()
        if user_count > 0:
            self.stdout.write(f'✓ Deleted {user_count} user records')

    def create_groups(self):
        """Create user groups"""
        groups = ['Admin', 'Teacher', 'Student', 'Parent']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
        self.stdout.write('✓ Created user groups')

    def create_academic_years(self):
        """Create or fetch academic years"""
        from django.utils import timezone
        current_year = timezone.now().year
        academic_years = []
        
        years_data = [
            {
                'name': f'{current_year-1}-{current_year}',
                'start_date': f'{current_year-1}-09-01',
                'end_date': f'{current_year}-08-31',
                'is_current': False
            },
            {
                'name': f'{current_year}-{current_year+1}',
                'start_date': f'{current_year}-09-01',
                'end_date': f'{current_year+1}-08-31',
                'is_current': True
            },
            {
                'name': f'{current_year+1}-{current_year+2}',
                'start_date': f'{current_year+1}-09-01',
                'end_date': f'{current_year+2}-08-31',
                'is_current': False
            }
        ]
        
        for year_data in years_data:
            ay, _ = AcademicYear.objects.get_or_create(
                name=year_data['name'],
                defaults=year_data
            )
            academic_years.append(ay)  # ✅ Always add to list
        
        self.stdout.write('✓ Created or fetched academic years')
        return academic_years

    def create_classes(self):
        """Create classes for Kenyan system"""
        classes_data = [
            # ECDE
            {'name': 'PP1', 'level_category': 'ECDE', 'grade_level': 'PP1', 'capacity': 25},
            {'name': 'PP2', 'level_category': 'ECDE', 'grade_level': 'PP2', 'capacity': 25},
            # Primary
            {'name': 'Grade 1', 'level_category': 'PRIMARY', 'grade_level': '1', 'capacity': 30},
            {'name': 'Grade 2', 'level_category': 'PRIMARY', 'grade_level': '2', 'capacity': 30},
            {'name': 'Grade 3', 'level_category': 'PRIMARY', 'grade_level': '3', 'capacity': 30},
            {'name': 'Grade 4', 'level_category': 'PRIMARY', 'grade_level': '4', 'capacity': 30},
            {'name': 'Grade 5', 'level_category': 'PRIMARY', 'grade_level': '5', 'capacity': 30},
            {'name': 'Grade 6', 'level_category': 'PRIMARY', 'grade_level': '6', 'capacity': 30},
            # Junior Secondary
            {'name': 'Grade 7', 'level_category': 'JUNIOR_SECONDARY', 'grade_level': '7', 'capacity': 35},
            {'name': 'Grade 8', 'level_category': 'JUNIOR_SECONDARY', 'grade_level': '8', 'capacity': 35},
            {'name': 'Grade 9', 'level_category': 'JUNIOR_SECONDARY', 'grade_level': '9', 'capacity': 35},
        ]
        
        classes = []
        for class_data in classes_data:
            class_obj, created = Class.objects.get_or_create(
                name=class_data['name'],
                defaults={
                    'level_category': class_data['level_category'],
                    'grade_level': class_data['grade_level'],
                    'capacity': class_data['capacity'],
                    'code': f"{class_data['level_category']}_{class_data['grade_level']}"
                }
            )
            classes.append(class_obj)
        
        self.stdout.write('✓ Created classes')
        return classes

    def create_sections(self, classes):
        """Create sections for classes - A, B, C, D for each class"""
        sections = []
        section_names = ['A', 'B', 'C', 'D']
        
        for class_obj in classes:
            for section_name in section_names:
                section, created = Section.objects.get_or_create(
                    name=section_name,
                    class_name=class_obj,
                    defaults={'capacity': class_obj.capacity // len(section_names)}
                )
                sections.append(section)
        
        self.stdout.write('✓ Created sections')
        return sections

    def create_subjects(self):
        """Create subjects for Kenyan curriculum"""
        subjects_data = [
            # Core subjects
            {'name': 'English', 'code': 'ENG'},
            {'name': 'Kiswahili', 'code': 'KIS'},
            {'name': 'Mathematics', 'code': 'MATH'},
            {'name': 'Science', 'code': 'SCI'},
            {'name': 'Social Studies', 'code': 'SST'},
            {'name': 'CRE', 'code': 'CRE'},
            {'name': 'IRE', 'code': 'IRE'},
            {'name': 'HRE', 'code': 'HRE'},
            # Optional subjects
            {'name': 'Agriculture', 'code': 'AGR'},
            {'name': 'Home Science', 'code': 'HSC'},
            {'name': 'Art and Craft', 'code': 'ART'},
            {'name': 'Music', 'code': 'MUS'},
            {'name': 'Physical Education', 'code': 'PE'},
            {'name': 'Computer Science', 'code': 'COMP'},
        ]
        
        subjects = []
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=subject_data['name'],
                defaults={'code': subject_data['code']}
            )
            subjects.append(subject)
        
        self.stdout.write('✓ Created subjects')
        return subjects

    def create_school_info(self):
        """Create school information"""
        school_info, created = SchoolInfo.objects.get_or_create(
            name="Petra Education Centre",
            defaults={
                'address': '123 School Road, Nairobi, Kenya',
                'phone': '+254-700-123456',
                'email': 'info@petra.edu',
                'established_date': '2010-01-15'
            }
        )
        self.stdout.write('✓ Created school information')

    def create_admin_user(self):
        """Create admin user"""
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@petra.edu',
                'first_name': 'School',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('✓ Created admin user (username: admin, password: admin123)')
        return admin_user

    def create_teachers(self, subjects):
        """Create teacher profiles"""
        teacher_names = [
            {'first': 'John', 'last': 'Kamau', 'gender': 'M', 'subjects': ['ENG', 'KIS']},
            {'first': 'Mary', 'last': 'Wanjiku', 'gender': 'F', 'subjects': ['MATH', 'SCI']},
            {'first': 'David', 'last': 'Ochieng', 'gender': 'M', 'subjects': ['SST', 'CRE']},
            {'first': 'Grace', 'last': 'Akinyi', 'gender': 'F', 'subjects': ['ART', 'MUS']},
            {'first': 'Peter', 'last': 'Mwangi', 'gender': 'M', 'subjects': ['PE', 'COMP']},
            {'first': 'Sarah', 'last': 'Njeri', 'gender': 'F', 'subjects': ['AGR', 'HSC']},
            {'first': 'James', 'last': 'Kipchoge', 'gender': 'M', 'subjects': ['ENG', 'SST']},
            {'first': 'Lucy', 'last': 'Wambui', 'gender': 'F', 'subjects': ['MATH', 'COMP']},
        ]
        
        teachers = []
        current_year = timezone.now().year
        
        for i, teacher_data in enumerate(teacher_names, 1):
            username = f"teacher{i}"
            email = f"{username}@petra.edu"
            
            # Create user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': teacher_data['first'],
                    'last_name': teacher_data['last'],
                }
            )
            if created:
                user.set_password('teacher123')
                user.save()
                
                # Add to Teacher group
                teacher_group = Group.objects.get(name='Teacher')
                user.groups.add(teacher_group)
            
            # Create teacher profile
            teacher, created = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'teacher_id': f"TCH-{current_year}-{i:04d}",
                    'first_name': teacher_data['first'],
                    'last_name': teacher_data['last'],
                    'gender': teacher_data['gender'],
                    'date_of_birth': f'{random.randint(1970, 1990)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                    'address': f'{random.randint(100, 999)} Teacher Street, Nairobi',
                    'phone': f'+2547{random.randint(10000000, 99999999)}',
                    'email': email,
                    'qualification': random.choice(['B.Ed', 'M.Ed', 'PGDE']),
                    'specialization': 'Education',
                    'experience': random.randint(2, 15),
                    'joining_date': f'{random.randint(2015, 2022)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                    'salary': random.randint(40000, 120000),
                    'teaching_level': random.choice(['PRIMARY', 'JUNIOR_SECONDARY', 'ALL']),
                }
            )
            
            # Assign subjects
            subject_codes = teacher_data['subjects']
            teacher_subjects = Subject.objects.filter(code__in=subject_codes)
            teacher.subjects.set(teacher_subjects)
            
            teachers.append(teacher)
        
        self.stdout.write('✓ Created teachers')
        return teachers

    def assign_class_teachers(self, classes, teachers):
        """Assign class teachers to classes"""
        for i, class_obj in enumerate(classes):
            if i < len(teachers):
                class_obj.class_teacher = teachers[i]
                class_obj.save()
        self.stdout.write('✓ Assigned class teachers')

    def create_parents_and_students(self, classes, sections):
        """Create parent and student profiles with proper family relationships"""
        parents = []
        students = []
        current_year = timezone.now().year
        
        # Kenyan family names and structures
        family_names = [
            {'surname': 'Maina', 'father': 'James', 'mother': 'Grace', 'kids': 2},
            {'surname': 'Kariuki', 'father': 'David', 'mother': 'Sarah', 'kids': 3},
            {'surname': 'Nyong\'o', 'father': 'Peter', 'mother': 'Ann', 'kids': 2},
            {'surname': 'Odhiambo', 'father': 'Michael', 'mother': 'Ruth', 'kids': 3},
            {'surname': 'Waweru', 'father': 'Stephen', 'mother': 'Mercy', 'kids': 2},
            {'surname': 'Kinyua', 'father': 'Eric', 'mother': 'Joy', 'kids': 3},
            {'surname': 'Mbugua', 'father': 'Victor', 'mother': 'Faith', 'kids': 2},
            {'surname': 'Gitonga', 'father': 'Samuel', 'mother': 'Hope', 'kids': 3},
            {'surname': 'Mwangi', 'father': 'Brian', 'mother': 'Linda', 'kids': 2},
            {'surname': 'Njoroge', 'father': 'Kevin', 'mother': 'Sharon', 'kids': 3},
        ]
        
        # Student first names by gender
        first_names_male = ['Brian', 'Kevin', 'Dennis', 'Michael', 'Stephen', 'Eric', 'Victor', 'Samuel', 'James', 'David']
        first_names_female = ['Mercy', 'Sharon', 'Linda', 'Ann', 'Ruth', 'Joy', 'Faith', 'Hope', 'Grace', 'Sarah']
        
        # Create parents (families)
        for i, family in enumerate(family_names, 1):
            # Create father user and profile
            father_username = f"parent_{family['surname'].lower()}_father"
            father_user, created = User.objects.get_or_create(
                username=father_username,
                defaults={
                    'email': f"{father_username}@gmail.com",
                    'first_name': family['father'],
                    'last_name': family['surname'],
                }
            )
            if created:
                father_user.set_password('parent123')
                father_user.save()
                parent_group = Group.objects.get(name='Parent')
                father_user.groups.add(parent_group)
            
            father_parent, created = Parent.objects.get_or_create(
                user=father_user,
                defaults={
                    'first_name': family['father'],
                    'last_name': family['surname'],
                    'phone': f'+2547{random.randint(10000000, 99999999)}',
                    'email': f"{father_username}@gmail.com",
                    'address': f'{random.randint(100, 999)} {family["surname"]} Family Road, Nairobi',
                    'occupation': random.choice(['Engineer', 'Doctor', 'Business', 'Teacher']),
                    'father_name': f'Mr. {family["surname"]}',
                    'mother_name': family['mother'],
                }
            )
            
            # Create mother user and profile
            mother_username = f"parent_{family['surname'].lower()}_mother"
            mother_user, created = User.objects.get_or_create(
                username=mother_username,
                defaults={
                    'email': f"{mother_username}@gmail.com",
                    'first_name': family['mother'],
                    'last_name': family['surname'],
                }
            )
            if created:
                mother_user.set_password('parent123')
                mother_user.save()
                parent_group = Group.objects.get(name='Parent')
                mother_user.groups.add(parent_group)
            
            mother_parent, created = Parent.objects.get_or_create(
                user=mother_user,
                defaults={
                    'first_name': family['mother'],
                    'last_name': family['surname'],
                    'phone': f'+2547{random.randint(10000000, 99999999)}',
                    'email': f"{mother_username}@gmail.com",
                    'address': f'{random.randint(100, 999)} {family["surname"]} Family Road, Nairobi',
                    'occupation': random.choice(['Nurse', 'Teacher', 'Business', 'Housewife']),
                    'father_name': f'Mr. {family["surname"]}',
                    'mother_name': family['mother'],
                }
            )
            
            parents.extend([father_parent, mother_parent])
            
            # Create children for this family (2-3 kids as specified)
            num_kids = family['kids']
            family_students = []
            
            for kid_num in range(1, num_kids + 1):
                gender = random.choice(['M', 'F'])
                first_name = random.choice(first_names_male if gender == 'M' else first_names_female)
                
                # Assign class - younger kids in lower classes, older in higher classes
                if num_kids == 1:
                    class_index = random.randint(0, len(classes)-1)
                else:
                    # Distribute kids across classes (younger in lower grades)
                    if kid_num == 1:
                        class_index = random.randint(0, 3)  # PP1-Grade 3
                    elif kid_num == 2:
                        class_index = random.randint(4, 7)  # Grade 4-Grade 7
                    else:
                        class_index = random.randint(8, len(classes)-1)  # Grade 8+
                
                class_obj = classes[class_index]
                
                # Get sections for this class and assign a random section (A, B, C, or D)
                class_sections = Section.objects.filter(class_name=class_obj)
                section = random.choice(list(class_sections)) if class_sections.exists() else None
                
                # Create student user (optional)
                student_user = None
                if random.choice([True, False]):  # 50% chance to create user
                    username = f"student_{family['surname'].lower()}_{kid_num}"
                    email = f"{username}@petra.edu"
                    
                    student_user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'first_name': first_name,
                            'last_name': family['surname'],
                        }
                    )
                    if created:
                        student_user.set_password('student123')
                        student_user.save()
                        student_group = Group.objects.get(name='Student')
                        student_user.groups.add(student_group)
                
                # Calculate birth year based on class level
                base_year = 2005 if class_index <= 3 else 2010  # Rough estimate
                birth_year = base_year + random.randint(-2, 2)
                
                # Create student profile
                student, created = Student.objects.get_or_create(
                    student_id=f"STU-{family['surname']}-{current_year}-{kid_num:02d}",
                    defaults={
                        'user': student_user,
                        'first_name': first_name,
                        'last_name': family['surname'],
                        'gender': gender,
                        'date_of_birth': f'{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                        'religion': random.choice(['Christian', 'Muslim', 'Other']),
                        'address': father_parent.address,  # Same address as parents
                        'phone': father_parent.phone,  # Same phone as parents
                        'email': f"{first_name.lower()}.{family['surname'].lower()}@petra.edu",
                        'current_class': class_obj,
                        'current_section': section,  # Always assign a section (A, B, C, or D)
                        'roll_number': f"RN{family['surname'][:3].upper()}{kid_num:02d}",
                        'admission_date': f'{random.randint(2018, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                        'father_name': f"{father_parent.first_name} {father_parent.last_name}",
                        'father_occupation': father_parent.occupation,
                        'father_phone': father_parent.phone,
                        'mother_name': f"{mother_parent.first_name} {mother_parent.last_name}",
                        'mother_occupation': mother_parent.occupation,
                        'mother_phone': mother_parent.phone,
                        'guardian_email': father_parent.email,
                        'guardian_phone': father_parent.phone,
                    }
                )
                
                family_students.append(student)
                students.append(student)
                
                # Link student to both parents
                father_parent.students.add(student)
                mother_parent.students.add(student)
            
            self.stdout.write(f'  ✓ Created {num_kids} students for {family["surname"]} family')
        
        # Print family relationship statistics
        family_stats = {}
        for student in students:
            student_parents = student.parents.all()
            if student_parents:
                parent_last_names = set(parent.last_name for parent in student_parents)
                for parent_name in parent_last_names:
                    if parent_name not in family_stats:
                        family_stats[parent_name] = 0
                    family_stats[parent_name] += 1
        
        self.stdout.write(f'✓ Created {len(parents)} parents and {len(students)} students')
        self.stdout.write('Family relationships:')
        for family_name, kid_count in family_stats.items():
            self.stdout.write(f'  - {family_name} family: {kid_count} children')
        
        # Section assignment statistics
        students_with_sections = [s for s in students if s.current_section is not None]
        students_without_sections = [s for s in students if s.current_section is None]
        
        self.stdout.write(f'Section assignment:')
        self.stdout.write(f'  - {len(students_with_sections)} students with sections')
        self.stdout.write(f'  - {len(students_without_sections)} students without sections')
        
        # Show section distribution
        section_distribution = {}
        for student in students_with_sections:
            section_name = student.current_section.name
            if section_name not in section_distribution:
                section_distribution[section_name] = 0
            section_distribution[section_name] += 1
        
        for section_name, count in section_distribution.items():
            self.stdout.write(f'  - Section {section_name}: {count} students')
        
        return parents, students

    def create_attendance(self, students):
        """Create attendance records for the past 30 days"""
        today = timezone.now().date()
        attendance_count = 0
        
        for i in range(30):
            date = today - timedelta(days=i)
            if date.weekday() < 5:  # Only weekdays
                for student in random.sample(students, min(40, len(students))):
                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        date=date,
                        defaults={
                            'status': random.choices([True, False], weights=[0.9, 0.1])[0],
                            'remarks': '' if random.random() > 0.1 else 'Late arrival'
                        }
                    )
                    if created:
                        attendance_count += 1
        
        self.stdout.write(f'✓ Created {attendance_count} attendance records')

    def create_exams_and_results(self, classes, subjects, students):
        """Create exams and results"""
        exam_types = ['MID', 'FINAL', 'QUIZ', 'ASSIGNMENT']
        exam_names = ['Mid-Term Examination', 'End of Term Exam', 'Class Test', 'Assignment']
        exam_count = 0
        result_count = 0
        
        for class_obj in classes:
            class_subjects = random.sample(list(subjects), min(5, len(subjects)))
            for subject in class_subjects:
                exam_type = random.choice(exam_types)
                exam_name = f"{class_obj.name} {subject.name} {exam_names[exam_types.index(exam_type)]}"
                total_marks = random.randint(40, 100)
                passing_marks = random.randint(20, total_marks - 10)  # always less than total

                exam, created = Exam.objects.get_or_create(
                    name=exam_name,
                    subject=subject,
                    class_name=class_obj,
                    defaults={
                        'exam_type': exam_type,
                        'exam_date': timezone.now().date() - timedelta(days=random.randint(1, 60)),
                        'total_marks': total_marks,
                        'passing_marks': passing_marks,
                    }
                )
                if created:
                    exam_count += 1
                
                # Create results for students in this class
                class_students = Student.objects.filter(current_class=class_obj)
                for student in class_students:
                    marks = random.randint(int(exam.passing_marks), int(exam.total_marks))
                    result, created = ExamResult.objects.get_or_create(
                        exam=exam,
                        student=student,
                        defaults={
                            'marks_obtained': marks,
                        }
                    )
                    if created:
                        result_count += 1
        
        self.stdout.write(f'✓ Created {exam_count} exams and {result_count} results')

    def create_fees_and_payments(self, students, academic_year):
        """Create fees and payment records"""
        fee_types = ['tuition', 'exam', 'transport', 'hostel', 'library', 'sports', 'activity']
        fee_names = {
            'tuition': 'Term Tuition Fee',
            'exam': 'Examination Fee',
            'transport': 'Transport Fee',
            'hostel': 'Boarding Fee',
            'library': 'Library Fee',
            'sports': 'Sports Fee',
            'activity': 'Activity Fee'
        }
        
        admin_user = User.objects.get(username='admin')
        fee_count = 0
        payment_count = 0
        
        for student in students:
            # Create 2-4 fee records per student
            for _ in range(random.randint(2, 4)):
                fee_type = random.choice(fee_types)
                fee_name = f"{student.current_class.name} {fee_names[fee_type]}"
                
                fee, created = Fee.objects.get_or_create(
                    student=student,
                    name=fee_name,
                    academic_year=academic_year,
                    defaults={
                        'class_level': student.current_class,
                        'fee_type': fee_type,
                        'amount': random.randint(1000, 10000),
                        'status': random.choices(['paid', 'unpaid'], weights=[0.7, 0.3])[0],
                        'due_date': timezone.now().date() + timedelta(days=random.randint(1, 30)),
                        'description': f"{fee_names[fee_type]} for {academic_year.name}",
                        'created_by': admin_user,
                    }
                )
                if created:
                    fee_count += 1
                
                # Create payment if fee is paid
                if fee.status == 'paid':
                    payment, created = FeePayment.objects.get_or_create(
                        student=student,
                        fee=fee,
                        defaults={
                            'amount_paid': fee.amount,
                            'payment_date': fee.due_date - timedelta(days=random.randint(1, 10)),
                            'payment_method': random.choice(['Cash', 'MPesa', 'Bank Transfer']),
                            'transaction_id': f"TXN{random.randint(100000, 999999)}",
                        }
                    )
                    if created:
                        payment_count += 1
        
        self.stdout.write(f'✓ Created {fee_count} fees and {payment_count} payments')

    def create_expenses(self):
        """Create expense records"""
        expense_types = ['salary', 'transport', 'maintenance', 'purchase', 'utilities', 'other']
        expense_names = {
            'salary': 'Staff Salaries',
            'transport': 'School Bus Maintenance',
            'maintenance': 'Building Repair',
            'purchase': 'Teaching Materials',
            'utilities': 'Electricity and Water Bill',
            'other': 'Miscellaneous Expenses'
        }
        
        admin_user = User.objects.get(username='admin')
        expense_count = 0
        
        for i in range(20):
            expense_type = random.choice(expense_types)
            expense, created = Expense.objects.get_or_create(
                name=f"{expense_names[expense_type]} - {timezone.now().strftime('%B %Y')}",
                defaults={
                    'expense_type': expense_type,
                    'amount': random.randint(5000, 50000),
                    'phone': f'+2547{random.randint(10000000, 99999999)}',
                    'email': f"vendor{i}@gmail.com",
                    'status': random.choice(['paid', 'pending', 'due']),
                    'date': timezone.now().date() - timedelta(days=random.randint(1, 60)),
                    'description': f"Payment for {expense_names[expense_type].lower()}",
                    'created_by': admin_user,
                }
            )
            if created:
                expense_count += 1
        
        self.stdout.write(f'✓ Created {expense_count} expense records')

    def create_notices(self):
        """Create notice records"""
        notices_data = [
            {
                'title': 'School Reopening Date',
                'content': 'All students should report back to school on 2nd January 2024. Ensure you have all the required materials and complete your fees payment.',
                'priority': 'HIGH',
                'target_audience': 'ALL'
            },
            {
                'title': 'Parent-Teacher Meeting',
                'content': 'There will be a parent-teacher meeting on 15th January 2024. All parents are requested to attend.',
                'priority': 'MEDIUM',
                'target_audience': 'PARENTS'
            },
            {
                'title': 'Sports Day Announcement',
                'content': 'Annual sports day will be held on 20th February 2024. Students should register with their class teachers.',
                'priority': 'MEDIUM',
                'target_audience': 'STUDENTS'
            },
            {
                'title': 'Staff Meeting',
                'content': 'All teaching staff are required to attend the staff meeting in the conference room at 3:00 PM.',
                'priority': 'LOW',
                'target_audience': 'TEACHERS'
            },
        ]
        
        admin_user = User.objects.get(username='admin')
        notice_count = 0
        
        for notice_data in notices_data:
            notice, created = Notice.objects.get_or_create(
                title=notice_data['title'],
                defaults={
                    'content': notice_data['content'],
                    'priority': notice_data['priority'],
                    'target_audience': notice_data['target_audience'],
                    'posted_by': admin_user,
                    'expiry_date': timezone.now().date() + timedelta(days=30),
                }
            )
            if created:
                notice_count += 1
        
        self.stdout.write(f'✓ Created {notice_count} notice records')

    def create_messages(self):
        """Create sample messages"""
        admin_user = User.objects.get(username='admin')
        teachers = Teacher.objects.all()[:3]
        message_count = 0
        
        for teacher in teachers:
            message, created = Message.objects.get_or_create(
                sender=admin_user,
                receiver=teacher.user,
                subject='Welcome to New Academic Year',
                defaults={
                    'content': f'Dear {teacher.first_name}, welcome to the new academic year. Please ensure all your lesson plans are ready.',
                    'is_read': random.choice([True, False]),
                }
            )
            if created:
                message_count += 1
        
        self.stdout.write(f'✓ Created {message_count} message records')