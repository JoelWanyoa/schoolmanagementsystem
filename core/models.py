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
        ('PP1', 'Pre-Primary 1'),
        ('PP2', 'Pre-Primary 2'),
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
        ('6', 'Grade 6'),
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
    
    class Meta:
        unique_together = ['name', 'class_name']
        ordering = ['class_name', 'name']
    
    def __str__(self):
        return f"{self.class_name} - Section {self.name}"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
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
    
    # Academic Information
    current_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    current_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True)
    roll_number = models.CharField(max_length=10)
    admission_date = models.DateField(default=timezone.now)
    
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

# ... (keep all other models the same)

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
    date = models.DateField(default=timezone.now)
    status = models.BooleanField(default=True)  # True for Present, False for Absent
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student']
    
    def __str__(self):
        status = "Present" if self.status else "Absent"
        return f"{self.student} - {self.date} - {status}"

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
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    exam_date = models.DateField()
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    passing_marks = models.DecimalField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} - {self.subject} - {self.class_name}"

class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    grade = models.CharField(max_length=5, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['exam', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.exam} - {self.marks_obtained}"
    
    def save(self, *args, **kwargs):
        # Calculate grade based on marks
        if self.marks_obtained and self.exam.total_marks:
            percentage = (self.marks_obtained / self.exam.total_marks) * 100
            if percentage >= 90:
                self.grade = 'A+'
            elif percentage >= 80:
                self.grade = 'A'
            elif percentage >= 70:
                self.grade = 'B'
            elif percentage >= 60:
                self.grade = 'C'
            elif percentage >= 50:
                self.grade = 'D'
            else:
                self.grade = 'F'
        super().save(*args, **kwargs)

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