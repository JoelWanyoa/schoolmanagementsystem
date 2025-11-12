# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import os
from django.urls import reverse

def student_photo_path(instance, filename):
    return f'students/photos/student_{instance.student_id}/{filename}'

def teacher_photo_path(instance, filename):
    return f'teachers/photos/teacher_{instance.teacher_id}/{filename}'

def parent_photo_path(instance, filename):
    return f'parents/photos/parent_{instance.id}/{filename}'

def school_logo_path(instance, filename):
    return f'school/logo/{filename}'

class SchoolInfo(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    logo = models.ImageField(upload_to=school_logo_path, null=True, blank=True)
    established_date = models.DateField()
    
    def __str__(self):
        return self.name

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one academic year is marked as current
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

class Class(models.Model):
    LEVEL_CATEGORIES = [
        ('ECDE', 'Early Childhood Development Education'),
        ('PRIMARY', 'Primary'),
        ('JUNIOR_SECONDARY', 'Junior Secondary'),
    ]
    
    GRADE_LEVELS = [
        # ECDE Levels
        ('PP1', 'Pre-Primary 1'),
        ('PP2', 'Pre-Primary 2'),
        
        # Primary Levels
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
        ('6', 'Grade 6'),
        
        # Junior Secondary Levels
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
    ]
    
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    level_category = models.CharField(max_length=20, choices=LEVEL_CATEGORIES)
    grade_level = models.CharField(max_length=3, choices=GRADE_LEVELS)
    capacity = models.IntegerField(default=30)
    class_teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['level_category', 'grade_level']
        verbose_name_plural = 'Classes'
    
    def __str__(self):
        return f"{self.get_level_category_display()} - {self.get_grade_level_display()}"
    
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.get_level_category_display()} - {self.get_grade_level_display()}"
        if not self.code:
            self.code = f"{self.level_category}_{self.grade_level}"
        super().save(*args, **kwargs)

class Section(models.Model):
    SECTION_CHOICES = [
        ('A', 'Section A'),
        ('B', 'Section B'),
        ('C', 'Section C'),
        ('D', 'Section D'),
        ('E', 'Section E'),
        ('F', 'Section F'),
    ]
    
    name = models.CharField(max_length=1, choices=SECTION_CHOICES)
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    capacity = models.IntegerField(default=30)
    room_number = models.CharField(max_length=20, blank=True, help_text="Room number for this section")  # Add this line
    
    class Meta:
        unique_together = ['name', 'class_name']
        ordering = ['class_name', 'name']
    
    def __str__(self):
        return f"{self.class_name} - Section {self.name}"
    
    @property
    def current_student_count(self):
        """Get the current number of students in this section"""
        return self.students.count()
    
    @property
    def available_seats(self):
        """Calculate available seats in this section"""
        return self.capacity - self.current_student_count
    
    @property
    def is_full(self):
        """Check if section is at full capacity"""
        return self.current_student_count >= self.capacity

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    credit_hours = models.IntegerField(default=1, help_text="Number of credit hours for this subject")
    
    def __str__(self):
        return self.name

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    religion = models.CharField(max_length=50, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to=student_photo_path, null=True, blank=True)
        
    # Parent Information
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100, blank=True)
    father_phone = models.CharField(max_length=15, blank=True)
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100, blank=True)
    mother_phone = models.CharField(max_length=15, blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_relationship = models.CharField(max_length=50, blank=True)
    
    # Previous School Information
    previous_school = models.CharField(max_length=200, blank=True)
    transfer_certificate_no = models.CharField(max_length=100, blank=True)
    
    # Medical Information
    medical_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    doctor_name = models.CharField(max_length=100, blank=True)
    doctor_phone = models.CharField(max_length=15, blank=True)
    
    # National ID/Birth Certificate
    national_id = models.CharField(max_length=50, blank=True)
    birth_certificate_no = models.CharField(max_length=50, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add these fields for online status
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)

    current_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    current_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, related_name='students')
    roll_number = models.CharField(max_length=10)
    admission_date = models.DateField(default=timezone.now)
    
    class Meta:
        ordering = ['current_class', 'roll_number']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def current_class_name(self):
        return self.current_class.name if self.current_class else "Not Assigned"
    
    @property
    def current_section_name(self):
        return f"Section {self.current_section.name}" if self.current_section else "Not Assigned"
    
    @property
    def level_category(self):
        return self.current_class.level_category if self.current_class else None
    
    def save(self, *args, **kwargs):
        if not self.student_id:
            year = timezone.now().year
            last_student = Student.objects.filter(admission_date__year=year).order_by('-id').first()
            if last_student:
                last_id = int(last_student.student_id.split('-')[-1])
                new_id = last_id + 1
            else:
                new_id = 1
            self.student_id = f"STU-{year}-{new_id:04d}"
        
        super().save(*args, **kwargs)

# models.py - Update the Parent model's students field

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    address = models.TextField()
    occupation = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to=parent_photo_path, null=True, blank=True)
    
    # Additional parent information
    father_name = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100, blank=True)
    
    # Children - FIXED: Use proper related_name
    students = models.ManyToManyField(Student, related_name='parents')  # Changed from 'student_parents' to 'parents'
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add these fields for online status
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Teacher(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    TEACHING_LEVELS = [
        ('ECDE', 'ECDE'),
        ('PRIMARY', 'Primary'),
        ('JUNIOR_SECONDARY', 'Junior Secondary'),
        ('ALL', 'All Levels'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    teacher_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    religion = models.CharField(max_length=50, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    photo = models.ImageField(upload_to=teacher_photo_path, null=True, blank=True)
    
    # Professional Information
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField(default=0)
    joining_date = models.DateField(default=timezone.now)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    teaching_level = models.CharField(max_length=20, choices=TEACHING_LEVELS, default='PRIMARY')
    
    # Subjects taught
    subjects = models.ManyToManyField(Subject)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add these fields for online status
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.teacher_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.teacher_id:
            year = timezone.now().year
            last_teacher = Teacher.objects.filter(joining_date__year=year).order_by('-id').first()
            if last_teacher:
                last_id = int(last_teacher.teacher_id.split('-')[-1])
                new_id = last_id + 1
            else:
                new_id = 1
            self.teacher_id = f"TCH-{year}-{new_id:04d}"
        super().save(*args, **kwargs)

class AdmissionForm(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    # Student Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Student.GENDER_CHOICES)
    student_photo = models.ImageField(upload_to='admission_photos/', null=True, blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    
    # Academic Information
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    previous_school = models.CharField(max_length=200, blank=True)
    transfer_certificate_no = models.CharField(max_length=100, blank=True)
    
    # Parent Information
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15)
    guardian_email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=15)
    emergency_relationship = models.CharField(max_length=50, blank=True)
    
    # Medical Information
    medical_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    doctor_name = models.CharField(max_length=100, blank=True)
    doctor_phone = models.CharField(max_length=15, blank=True)
    
    # Parent Login Information
    parent_username = models.CharField(max_length=150)
    parent_email = models.EmailField()
    parent_password = models.CharField(max_length=128)
    
    # Auto-generated fields (FIXED: Rename student_id to avoid clash)
    admission_student_id = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Student ID")
    roll_number = models.CharField(max_length=10, blank=True, null=True)
    parent_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='admission_forms'
    )
    
    # Status and tracking (FIXED: Rename student field to avoid clash)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    submitted_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_admissions')
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_student = models.OneToOneField(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='admission_form', verbose_name="Student")
    
    class Meta:
        ordering = ['-submitted_date']
    
    def __str__(self):
        return f"Admission: {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def parent(self):
        """Property to get parent profile for admin display"""
        if self.parent_user and hasattr(self.parent_user, 'parent'):
            return self.parent_user.parent
        return None
    
    def approve_admission(self, approved_by):
        """Create student and parent accounts from admission form"""
        try:
            # Generate student username
            student_username = self.admission_student_id.lower()
            
            # Create student user with temporary password
            student_user = User.objects.create_user(
                username=student_username,
                password='student123',
                first_name=self.first_name,
                last_name=self.last_name,
                email=f"{student_username}@petra.edu"
            )
            
            # Add student to Student group
            from django.contrib.auth.models import Group
            student_group, created = Group.objects.get_or_create(name='Student')
            student_user.groups.add(student_group)
            
            # Create student profile
            student = Student.objects.create(
                user=student_user,
                student_id=self.admission_student_id,  # Use the renamed field
                first_name=self.first_name,
                last_name=self.last_name,
                gender=self.gender,
                date_of_birth=self.date_of_birth,
                address=self.address,
                current_class=self.class_level,
                current_section=self.section,
                roll_number=self.roll_number,
                admission_date=timezone.now().date(),
                # Parent information
                father_name=self.father_name,
                father_occupation=self.father_occupation,
                mother_name=self.mother_name,
                mother_occupation=self.mother_occupation,
                guardian_email=self.guardian_email,
                guardian_phone=self.guardian_phone,
                emergency_contact_name=self.emergency_contact_name,
                emergency_contact_phone=self.emergency_contact_phone,
                previous_school=self.previous_school,
                transfer_certificate_no=self.transfer_certificate_no,
                medical_conditions=self.medical_conditions,
                medications=self.medications,
                doctor_name=self.doctor_name,
                doctor_phone=self.doctor_phone,
                national_id=self.national_id,
            )
            
            # Handle photo if exists
            if self.student_photo:
                student.photo = self.student_photo
                student.save()
            
            # Link student to parent if parent user exists
            if self.parent_user and hasattr(self.parent_user, 'parent'):
                self.parent_user.parent.students.add(student)
            
            self.approved_student = student  # Use the renamed field
            self.status = 'APPROVED'
            self.approved_by = approved_by
            self.approved_date = timezone.now()
            self.save()
            
            return True
            
        except Exception as e:
            print(f"Error in approve_admission: {e}")
            import traceback
            print(traceback.format_exc())
            if 'student_user' in locals():
                student_user.delete()
            return False

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.BooleanField(default=True)  # True for present, False for absent
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student__roll_number']
    
    def __str__(self):
        status = "Present" if self.status else "Absent"
        return f"{self.student.full_name} - {self.date} - {status}"

class Exam(models.Model):
    EXAM_TYPES = [
        ('MID', 'Mid Term'),
        ('FINAL', 'Final'),
        ('QUIZ', 'Quiz'),
        ('ASSIGNMENT', 'Assignment'),
    ]
    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE)
    exam_date = models.DateField()
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    passing_marks = models.DecimalField(max_digits=6, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} - {self.subject} - {self.class_level}"

# In core/models.py - Update the ExamResult model
class ExamResult(models.Model):
    GRADES = (
        ('A', 'A (Excellent)'),
        ('B', 'B (Very Good)'),
        ('C', 'C (Good)'),
        ('D', 'D (Pass)'),
        ('E', 'E (Fail)'),
        ('F', 'F (Fail)'),
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    grade = models.CharField(max_length=1, choices=GRADES, blank=True)
    position = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        ordering = ['-marks_obtained']
    
    def get_subject_specific_remark(self):
        """Get subject-appropriate default remark"""
        subject_name = self.exam.subject.name.lower() if self.exam and self.exam.subject else ""
        marks_float = float(self.marks_obtained)
        total_marks = float(self.exam.total_marks) if self.exam else 100
        percentage = (marks_float / total_marks) * 100
        
        # Base remarks by performance level
        if percentage >= 90:
            base_remark = "Outstanding performance! "
        elif percentage >= 80:
            base_remark = "Excellent work! "
        elif percentage >= 70:
            base_remark = "Very good performance. "
        elif percentage >= 60:
            base_remark = "Good effort. "
        elif percentage >= 50:
            base_remark = "Satisfactory performance. "
        elif percentage >= 40:
            base_remark = "Needs improvement. "
        else:
            base_remark = "Requires significant improvement. "
        
        # Subject-specific additions
        subject_keywords = {
            'math': "Strong problem-solving skills." if percentage >= 60 else "Needs practice in problem-solving.",
            'english': "Good language expression." if percentage >= 60 else "Focus on grammar and vocabulary.",
            'science': "Good scientific understanding." if percentage >= 60 else "Work on scientific concepts.",
            'physics': "Good analytical thinking." if percentage >= 60 else "Understand physical principles better.",
            'chemistry': "Good practical knowledge." if percentage >= 60 else "Practice chemical concepts.",
            'biology': "Good memory and understanding." if percentage >= 60 else "Study biological processes.",
            'history': "Good historical analysis." if percentage >= 60 else "Focus on historical events.",
            'geography': "Good geographical knowledge." if percentage >= 60 else "Study geographical concepts.",
            'kiswahili': "Umeweza vizuri." if percentage >= 60 else "Hitaji kujitahidi zaidi.",
        }
        
        # Find matching subject keyword
        subject_remark = ""
        for keyword, remark in subject_keywords.items():
            if keyword in subject_name:
                subject_remark = remark
                break
        
        return base_remark + subject_remark if subject_remark else base_remark + "Continue regular practice."
    
    def save(self, *args, **kwargs):
        # Calculate grade based on marks
        marks_float = float(self.marks_obtained)
        
        if marks_float >= 80:
            self.grade = 'A'
        elif marks_float >= 70:
            self.grade = 'B'
        elif marks_float >= 60:
            self.grade = 'C'
        elif marks_float >= 50:
            self.grade = 'D'
        elif marks_float >= 40:
            self.grade = 'E'
        else:
            self.grade = 'F'
        
        # Set default remark if empty
        if not self.remarks:
            self.remarks = self.get_subject_specific_remark()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student} - {self.exam}: {self.marks_obtained}"

class ReportCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.CharField(max_length=20, choices=(
        ('TERM1', 'First Term'),
        ('TERM2', 'Second Term'),
        ('TERM3', 'Third Term'),
    ))
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    average_score = models.DecimalField(max_digits=5, decimal_places=2)
    class_position = models.IntegerField()
    overall_grade = models.CharField(max_length=1)
    teacher_remarks = models.TextField()
    principal_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Report Card - {self.student} - {self.term}"

class Assignment(models.Model):
    ASSIGNMENT_TYPES = (
        ('HOMEWORK', 'Homework'),
        ('PROJECT', 'Project'),
        ('QUIZ', 'Quiz'),
        ('ESSAY', 'Essay'),
        ('PRESENTATION', 'Presentation'),
    )
    
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments')
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='HOMEWORK')
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    due_date = models.DateTimeField()
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.class_level.name}"
    
    @property
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    @property
    def submitted_count(self):
        """Count how many students have submitted this assignment"""
        return self.submissions.filter(submitted=True).count()
    
    @property
    def total_students(self):
        """Get total number of students in the class"""
        if hasattr(self.class_level, 'students'):
            return self.class_level.students.filter(is_active=True).count()
        return 0
    
    @property
    def submission_rate(self):
        """Calculate submission rate as percentage"""
        if self.total_students > 0:
            return (self.submitted_count / self.total_students) * 100
        return 0

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    submission_file = models.FileField(upload_to='assignment_submissions/', blank=True, null=True)
    submission_text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}"
    
    @property
    def is_late(self):
        if self.submitted_at and self.assignment.due_date:
            return self.submitted_at > self.assignment.due_date
        return False

class PromotionHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='promotions')
    from_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='promoted_from')
    from_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='promoted_from_section')
    to_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='promoted_to')
    to_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='promoted_to_section')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    promotion_date = models.DateTimeField(auto_now_add=True)
    promoted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name_plural = "Promotion History"
        ordering = ['-promotion_date']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.from_class.name} to {self.to_class.name}"

        
class Fee(models.Model):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    )
    
    FEE_TYPES = (
        ('tuition', 'Tuition Fee'),
        ('exam', 'Exam Fee'),
        ('transport', 'Transport Fee'),
        ('hostel', 'Hostel Fee'),
        ('library', 'Library Fee'),
        ('sports', 'Sports Fee'),
        ('activity', 'Activity Fee'),
        ('lab', 'Lab Fee'),
        ('other', 'Other Fee'),
    )
    
    # CORRECTED: Removed class_name field and used class_level consistently
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='fees')
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="Class Level")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, default=1)
    
    name = models.CharField(max_length=100)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    due_date = models.DateField()
    paid_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fee'
        verbose_name_plural = 'Fees'
    
    def __str__(self):
        return f"{self.name} - {self.class_level} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if self.status == 'paid' and not self.paid_date:
            self.paid_date = timezone.now().date()
        if self.status == 'unpaid' and self.paid_date:
            self.paid_date = None
        super().save(*args, **kwargs)
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.status == 'unpaid' and self.due_date < timezone.now().date()
    
    def get_fee_type_display(self):
        return dict(self.FEE_TYPES).get(self.fee_type, self.fee_type)

class Reminder(models.Model):
    REMINDER_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both'),
    ]
    
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name='reminders')
    student_name = models.CharField(max_length=200)
    fee_type = models.CharField(max_length=100)
    sent_date = models.DateTimeField(auto_now_add=True)
    sent_via = models.CharField(max_length=50, choices=REMINDER_METHODS, default='email')
    status = models.CharField(max_length=20, default='sent')
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_date']
    
    def __str__(self):
        return f"Reminder for {self.student_name} - {self.sent_date.strftime('%Y-%m-%d %H:%M')}"

class Expense(models.Model):
    EXPENSE_TYPES = (
        ('salary', 'Salary'),
        ('transport', 'Transport'),
        ('maintenance', 'Maintenance'),
        ('purchase', 'Purchase'),
        ('utilities', 'Utilities'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('due', 'Due'),
        ('others', 'Others'),
    )
    
    name = models.CharField(max_length=200, verbose_name="Expense Name")
    expense_id = models.CharField(max_length=50, unique=True, verbose_name="Expense ID")
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES, verbose_name="Expense Type")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    date = models.DateField(verbose_name="Expense Date")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['expense_type']),
            models.Index(fields=['status']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.name} - ${self.amount} - {self.get_expense_type_display()}"
    
    @property
    def status_class(self):
        status_classes = {
            'paid': 'success',
            'pending': 'warning',
            'due': 'danger',
            'others': 'secondary'
        }
        return status_classes.get(self.status, 'secondary')
    
    @property
    def formatted_amount(self):
        return f"${self.amount:,.2f}"
    
    def get_absolute_url(self):
        return reverse('expense_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.expense_id:
            year = timezone.now().year
            last_expense = Expense.objects.filter(date__year=year).order_by('-id').first()
            if last_expense:
                last_id = int(last_expense.expense_id.split('-')[-1])
                new_id = last_id + 1
            else:
                new_id = 1
            self.expense_id = f"EXP-{year}-{new_id:04d}"
        super().save(*args, **kwargs)

class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=50, default='Cash')
    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.student} - {self.fee} - ${self.amount_paid}"

class Notice(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
    ]
    AUDIENCE_CHOICES = [
        ('ALL', 'Everyone'),
        ('TEACHERS', 'Teachers Only'),
        ('STUDENTS', 'Students Only'),
        ('PARENTS', 'Parents Only'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField(max_length=2000)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    target_audience = models.CharField(max_length=15, choices=AUDIENCE_CHOICES, default='ALL')
    publish_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_notices')
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

# In core/models.py, update the Message model
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    file = models.FileField(upload_to='message_files/', blank=True, null=True)  # Add this line
    sent_date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_date']
    
    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"

# Signal to create user profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    pass

# Add these missing models to your models.py file

class Timetable(models.Model):
    DAY_CHOICES = [
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
    ]
    
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='timetable_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day', 'start_time']
        unique_together = ['class_level', 'day', 'start_time']
    
    def __str__(self):
        return f"{self.class_level} - {self.day} - {self.subject}"

class Book(models.Model):
    CATEGORY_CHOICES = [
        ('TEXTBOOK', 'Textbook'),
        ('REFERENCE', 'Reference Book'),
        ('STORY', 'Story Book'),
        ('SCIENCE', 'Science'),
        ('MATHEMATICS', 'Mathematics'),
        ('LANGUAGE', 'Language'),
        ('HISTORY', 'History'),
        ('GEOGRAPHY', 'Geography'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('BORROWED', 'Borrowed'),
        ('RESERVED', 'Reserved'),
        ('LOST', 'Lost'),
        ('DAMAGED', 'Damaged'),
    ]
    
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    publisher = models.CharField(max_length=100, blank=True)
    published_date = models.DateField(null=True, blank=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')  # Add this field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title', 'author']
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def save(self, *args, **kwargs):
        # Ensure available copies don't exceed total copies
        if self.available_copies > self.total_copies:
            self.available_copies = self.total_copies
        
        # Update status based on available copies
        if self.available_copies == 0:
            self.status = 'BORROWED'
        elif self.available_copies > 0 and self.status == 'BORROWED':
            self.status = 'AVAILABLE'
            
        super().save(*args, **kwargs)
    
    @property
    def is_available(self):
        return self.available_copies > 0
    
    @property
    def borrowed_count(self):
        return self.total_copies - self.available_copies

class BookBorrowing(models.Model):
    STATUS_CHOICES = [
        ('BORROWED', 'Borrowed'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
        ('LOST', 'Lost'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowings')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_borrowings')
    borrowed_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='BORROWED')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-borrowed_date']
    
    def __str__(self):
        return f"{self.book.title} - {self.borrower.get_full_name()}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status == 'BORROWED'
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

class TransportRoute(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    distance = models.DecimalField(max_digits=6, decimal_places=2, help_text="Distance in kilometers")
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_point} to {self.end_point})"

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('BUS', 'Bus'),
        ('VAN', 'Van'),
        ('CAR', 'Car'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('INACTIVE', 'Inactive'),
    ]
    
    vehicle_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    capacity = models.IntegerField()
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPES, default='BUS')
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=15)
    insurance_expiry = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    route = models.ForeignKey(TransportRoute, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.vehicle_number} - {self.model}"
    
    @property
    def is_insurance_expired(self):
        return self.insurance_expiry < timezone.now().date()

class Hostel(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=[('BOYS', 'Boys'), ('GIRLS', 'Girls')])
    address = models.TextField()
    warden_name = models.CharField(max_length=100)
    warden_phone = models.CharField(max_length=15)
    total_rooms = models.IntegerField()
    available_rooms = models.IntegerField()
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class HostelRoom(models.Model):
    ROOM_TYPES = [
        ('SINGLE', 'Single'),
        ('DOUBLE', 'Double'),
        ('TRIPLE', 'Triple'),
        ('DORMITORY', 'Dormitory'),
    ]
    
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Under Maintenance'),
    ]
    
    room_number = models.CharField(max_length=20)
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    capacity = models.IntegerField()
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    cost_per_student = models.DecimalField(max_digits=8, decimal_places=2)
    facilities = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='AVAILABLE')
    
    class Meta:
        unique_together = ['hostel', 'room_number']
    
    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"
    
    @property
    def available_beds(self):
        allocated_count = self.allocations.filter(status='ACTIVE').count()
        return self.capacity - allocated_count

class HostelAllocation(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hostel_allocations')
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name='allocations')
    allocated_date = models.DateField(default=timezone.now)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'status']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.room.room_number}"

class GradingSystem(models.Model):
    name = models.CharField(max_length=50)
    min_mark = models.DecimalField(max_digits=5, decimal_places=2)
    max_mark = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=5)
    points = models.DecimalField(max_digits=3, decimal_places=2)
    remarks = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['min_mark']
        verbose_name_plural = "Grading Systems"
    
    def __str__(self):
        return f"{self.grade} ({self.min_mark}-{self.max_mark})"

class TeacherPayment(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('MOBILE_MONEY', 'Mobile Money'),
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS, default='BANK_TRANSFER')
    month = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    year = models.IntegerField()
    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
        unique_together = ['teacher', 'month', 'year']
    
    def __str__(self):
        return f"{self.teacher.full_name} - {self.month}/{self.year} - ${self.amount}"

class Event(models.Model):
    EVENT_TYPES = [
        ('ACADEMIC', 'Academic'),
        ('SPORTS', 'Sports'),
        ('CULTURAL', 'Cultural'),
        ('HOLIDAY', 'Holiday'),
        ('MEETING', 'Meeting'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    event_type = models.CharField(max_length=15, choices=EVENT_TYPES, default='ACADEMIC')
    location = models.CharField(max_length=100, blank=True)
    target_audience = models.CharField(max_length=15, choices=Notice.AUDIENCE_CHOICES, default='ALL')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()
    
    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

class InventoryItem(models.Model):
    CATEGORIES = [
        ('STATIONERY', 'Stationery'),
        ('FURNITURE', 'Furniture'),
        ('EQUIPMENT', 'Equipment'),
        ('LAB', 'Lab Equipment'),
        ('SPORTS', 'Sports Equipment'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock = models.IntegerField(default=0)
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    last_restocked = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.quantity} in stock)"
    
    @property
    def total_value(self):
        return self.quantity * self.unit_price
    
    @property
    def needs_restock(self):
        return self.quantity <= self.minimum_stock

class LibraryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('BORROW', 'Borrow'),
        ('RETURN', 'Return'),
        ('RENEW', 'Renew'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    returned_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.book.title} - {self.member.get_full_name()}"

class StudentMedicalRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='medical_record')
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    emergency_medication = models.TextField(blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    last_checkup = models.DateField(null=True, blank=True)
    next_checkup = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Medical Record - {self.student.full_name}"

class Staff(models.Model):
    STAFF_TYPES = [
        ('ADMIN', 'Administrative'),
        ('SUPPORT', 'Support Staff'),
        ('SECURITY', 'Security'),
        ('CLEANING', 'Cleaning Staff'),
        ('OTHER', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    staff_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    staff_type = models.CharField(max_length=15, choices=STAFF_TYPES)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    joining_date = models.DateField(default=timezone.now)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.staff_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.staff_id:
            year = timezone.now().year
            last_staff = Staff.objects.filter(joining_date__year=year).order_by('-id').first()
            if last_staff:
                last_id = int(last_staff.staff_id.split('-')[-1])
                new_id = last_id + 1
            else:
                new_id = 1
            self.staff_id = f"STF-{year}-{new_id:04d}"
        super().save(*args, **kwargs)