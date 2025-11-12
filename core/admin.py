from django.contrib import admin
from .models import *

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'fee_type', 'class_level', 'amount', 'academic_year', 'status', 'due_date', 'created_by']
    list_filter = ['fee_type', 'status', 'class_level', 'academic_year', 'due_date']
    search_fields = ['name', 'description']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'class_level', 'academic_year')
        }),
        ('Fee Details', {
            'fields': ('fee_type', 'amount', 'status', 'due_date', 'paid_date', 'description')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'student_id', 'current_class', 'current_section', 'roll_number', 'gender', 'is_active']
    list_filter = ['current_class', 'current_section', 'gender', 'is_active', 'admission_date']
    search_fields = ['first_name', 'last_name', 'student_id', 'father_name', 'mother_name']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['current_class', 'current_section']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'student_id', 'gender', 'date_of_birth', 
                'religion', 'photo', 'national_id'
            )
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Academic Information', {
            'fields': ('current_class', 'current_section', 'roll_number', 'admission_date')
        }),
        ('Parent Information', {
            'fields': (
                'father_name', 'father_occupation', 'father_phone',
                'mother_name', 'mother_occupation', 'mother_phone',
                'guardian_email', 'guardian_phone'
            )
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_relationship')
        }),
        ('Medical Information', {
            'fields': ('medical_conditions', 'medications', 'doctor_name', 'doctor_phone'),
            'classes': ('collapse',)
        }),
        ('Previous School', {
            'fields': ('previous_school', 'transfer_certificate_no'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'teacher_id', 'qualification', 'specialization', 'experience', 'is_active']
    list_filter = ['gender', 'is_active', 'joining_date']
    search_fields = ['first_name', 'last_name', 'teacher_id', 'email']
    filter_horizontal = ['subjects']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'teacher_id', 'gender', 'date_of_birth',
                'religion', 'photo'
            )
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Professional Information', {
            'fields': ('qualification', 'specialization', 'experience', 'joining_date', 'salary', 'subjects')
        }),
        ('System Information', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'occupation']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    filter_horizontal = ['students']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone', 'email', 'photo')
        }),
        ('Additional Information', {
            'fields': ('address', 'occupation', 'father_name', 'mother_name')
        }),
        ('Children', {
            'fields': ('students',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AdmissionForm)
class AdmissionFormAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'class_level', 'section', 'status', 'submitted_date', 'admission_student_id']
    list_filter = ['status', 'class_level', 'section', 'submitted_date']
    search_fields = ['first_name', 'last_name', 'father_name', 'guardian_phone', 'admission_student_id']
    readonly_fields = ['submitted_date', 'approved_date', 'approved_student', 'parent_display', 'admission_student_id', 'roll_number']
    list_editable = ['status']
    
    fieldsets = (
        ('Student Information', {
            'fields': (
                'first_name', 'last_name', 'date_of_birth', 'gender', 'student_photo', 'national_id'
            )
        }),
        ('Academic Information', {
            'fields': ('class_level', 'section', 'previous_school', 'transfer_certificate_no')
        }),
        ('Parent Information', {
            'fields': (
                'father_name', 'father_occupation', 'mother_name', 'mother_occupation',
                'guardian_phone', 'guardian_email', 'address', 'city', 'postal_code'
            )
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_relationship')
        }),
        ('Medical Information', {
            'fields': ('medical_conditions', 'medications', 'doctor_name', 'doctor_phone'),
            'classes': ('collapse',)
        }),
        ('Parent Login', {
            'fields': ('parent_username', 'parent_email', 'parent_password')
        }),
        ('Auto-generated Information', {
            'fields': ('admission_student_id', 'roll_number'),
            'classes': ('collapse',)
        }),
        ('Application Status', {
            'fields': ('status', 'approved_by', 'approved_date', 'approved_student', 'parent_display')
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Student Name'
    
    def parent_display(self, obj):
        if obj.parent:
            return str(obj.parent)
        return "Not created"
    parent_display.short_description = 'Parent Account'
    
    actions = ['approve_admissions']
    
    def approve_admissions(self, request, queryset):
        for admission in queryset.filter(status='PENDING'):
            admission.approve_admission(request.user)
        self.message_user(request, f"Successfully approved {queryset.count()} admissions.")
    approve_admissions.short_description = "Approve selected admissions"

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'expense_type', 'amount', 'status', 'date', 'created_by']
    list_filter = ['expense_type', 'status', 'date']
    search_fields = ['name', 'expense_id', 'description']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Expense Information', {
            'fields': ('name', 'expense_id', 'expense_type', 'amount', 'status', 'date')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'capacity', 'class_teacher']
    list_filter = ['capacity']
    search_fields = ['name', 'code']
    list_select_related = ['class_teacher']

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_name', 'capacity']
    list_filter = ['class_name']
    search_fields = ['name', 'class_name__name']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current']
    list_editable = ['is_current']
    list_filter = ['is_current']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'remarks']
    list_filter = ['date', 'status']
    search_fields = ['student__first_name', 'student__last_name']
    list_select_related = ['student']
    date_hierarchy = 'date'

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'exam_type', 'subject', 'class_level', 'exam_date', 'total_marks']
    list_filter = ['exam_type', 'subject', 'class_level', 'exam_date']  # Changed 'class_name' to 'class_level'
    search_fields = ['name', 'subject__name']
    list_select_related = ['subject', 'class_level']

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'marks_obtained', 'grade']
    list_filter = ['exam', 'grade']
    search_fields = ['student__first_name', 'student__last_name', 'exam__name']
    list_select_related = ['student', 'exam']

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee', 'amount_paid', 'payment_date', 'payment_method']
    list_filter = ['payment_date', 'payment_method']
    search_fields = ['student__first_name', 'student__last_name', 'fee__name']
    list_select_related = ['student', 'fee']
    date_hierarchy = 'payment_date'

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'target_audience', 'publish_date', 'is_active']
    list_filter = ['priority', 'target_audience', 'is_active', 'publish_date']
    search_fields = ['title', 'content']
    list_editable = ['is_active']
    readonly_fields = ['publish_date', 'updated_at']
    
    fieldsets = (
        ('Notice Information', {
            'fields': ('title', 'content', 'priority', 'target_audience')
        }),
        ('Publication', {
            'fields': ('publish_date', 'expiry_date', 'is_active')
        }),
        ('Author', {
            'fields': ('posted_by',)
        }),
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'subject', 'sent_date', 'is_read']
    list_filter = ['sent_date', 'is_read']
    search_fields = ['sender__username', 'receiver__username', 'subject', 'content']
    list_select_related = ['sender', 'receiver']
    readonly_fields = ['sent_date']
    date_hierarchy = 'sent_date'

@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'established_date']

# You can also use admin.site.register for models that don't need custom configuration
# admin.site.register(SchoolInfo, SchoolInfoAdmin)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'total_copies', 'available_copies', 'status']
    list_filter = ['category', 'status']
    search_fields = ['title', 'author', 'isbn']

@admin.register(BookBorrowing)
class BookBorrowingAdmin(admin.ModelAdmin):
    list_display = ['book', 'borrower', 'borrowed_date', 'due_date', 'status', 'is_overdue']
    list_filter = ['status', 'borrowed_date']
    search_fields = ['book__title', 'borrower__username']