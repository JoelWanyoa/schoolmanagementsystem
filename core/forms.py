from django import forms
from .models import *
from django.utils import timezone

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'name', 
            'expense_id', 
            'expense_type', 
            'amount', 
            'phone', 
            'email', 
            'status', 
            'date', 
            'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter name',
                'required': 'required'
            }),
            'expense_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ID number',
                'required': 'required'
            }),
            'expense_type': forms.Select(attrs={
                'class': 'form-control select2',
                'required': 'required'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '0',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control textarea',
                'rows': 4,
                'placeholder': 'Enter description (optional)'
            }),
        }
        labels = {
            'name': 'Name *',
            'expense_id': 'ID No *',
            'expense_type': 'Expense Type *',
            'amount': 'Amount *',
            'phone': 'Phone',
            'email': 'E-Mail Address',
            'status': 'Status',
            'date': 'Date',
            'description': 'Description',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value for date to today if not provided
        if not self.instance.pk and not self.data.get('date'):
            self.initial['date'] = timezone.now().date()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_expense_id(self):
        expense_id = self.cleaned_data.get('expense_id')
        if expense_id:
            # Check if expense_id already exists (excluding current instance)
            query = Expense.objects.filter(expense_id=expense_id)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError("An expense with this ID already exists.")
        return expense_id

class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['student', 'class_level', 'name', 'academic_year', 'fee_type', 'amount', 'status', 'due_date', 'paid_date', 'description']
        widgets = {
            'student': forms.HiddenInput(),  # Make student field hidden
            'class_level': forms.HiddenInput(),  # Make class_level field hidden
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter fee name',
                'required': 'required'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-control select2',
                'required': 'required'
            }),
            'fee_type': forms.Select(attrs={
                'class': 'form-control select2',
                'required': 'required'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '0',
                'required': 'required'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': 'required'
            }),
            'paid_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control textarea',
                'rows': 4,
                'placeholder': 'Enter description (optional)'
            }),
        }
        labels = {
            'name': 'Fee Name *',
            'class_level': 'Class',
            'academic_year': 'Academic Year *',
            'fee_type': 'Fee Type *',
            'amount': 'Amount *',
            'status': 'Status',
            'due_date': 'Due Date *',
            'paid_date': 'Paid Date',
            'description': 'Description',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make class_level not required since it will be auto-populated
        self.fields['class_level'].required = False
        
        # Set default due date to 30 days from now if not provided
        if not self.instance.pk and not self.data.get('due_date'):
            default_due_date = timezone.now().date() + timezone.timedelta(days=30)
            self.initial['due_date'] = default_due_date
        
        # Set initial status to unpaid
        if not self.instance.pk:
            self.initial['status'] = 'unpaid'

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year and 'academic_year' in self.fields:
            self.fields['academic_year'].initial = current_year

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_paid_date(self):
        status = self.cleaned_data.get('status')
        paid_date = self.cleaned_data.get('paid_date')
        
        if status == 'paid' and not paid_date:
            raise forms.ValidationError("Paid date is required when status is 'Paid'.")
        
        if paid_date and paid_date > timezone.now().date():
            raise forms.ValidationError("Paid date cannot be in the future.")
        
        return paid_date

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        paid_date = cleaned_data.get('paid_date')
        due_date = cleaned_data.get('due_date')

        if status == 'paid' and paid_date and due_date and paid_date > due_date:
            raise forms.ValidationError("Paid date cannot be after the due date.")

        return cleaned_data

# Additional forms for other models
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'admission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = '__all__'
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = '__all__'
        exclude = ['user', 'created_at', 'updated_at']

class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'subject', 'class_level', 'assignment_type', 
                 'total_marks', 'due_date', 'attachment', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        if self.teacher:
            # Filter subjects to only those the teacher teaches
            self.fields['subject'].queryset = self.teacher.subjects.all()
            
            # Filter classes - show classes teacher teaches OR all classes if none assigned
            teacher_classes = Class.objects.filter(class_teacher=self.teacher)
            if teacher_classes.exists():
                self.fields['class_level'].queryset = teacher_classes
            else:
                # Fallback: show all classes if teacher has no assigned classes
                self.fields['class_level'].queryset = Class.objects.all()
                
            # Add helpful text
            self.fields['class_level'].help_text = "Select the class for this assignment"

class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_file', 'submission_text']
        widgets = {
            'submission_text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your submission here...'}),
        }

# In core/forms.py - Update the ExamForm
class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'exam_type', 'subject', 'class_level', 'exam_date', 'total_marks', 'passing_marks']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter exam name'}),
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'class_level': forms.Select(attrs={'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'step': '0.5',
                'placeholder': 'e.g., 100'
            }),
            'passing_marks': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.5',
                'placeholder': 'e.g., 40'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        # Make fields required
        self.fields['name'].required = True
        self.fields['exam_type'].required = True
        self.fields['subject'].required = True
        self.fields['class_level'].required = True
        self.fields['exam_date'].required = True
        self.fields['total_marks'].required = True
        self.fields['passing_marks'].required = True
        
        # Set initial values and filter options if teacher is provided
        if teacher:
            # Filter subjects
            if hasattr(teacher, 'subjects'):
                self.fields['subject'].queryset = teacher.subjects.all()
            else:
                self.fields['subject'].queryset = Subject.objects.all()
            
            # Filter classes
            self.fields['class_level'].queryset = Class.objects.filter(class_teacher=teacher)
            
            # Set initial values if only one option exists
            if self.fields['subject'].queryset.count() == 1:
                self.fields['subject'].initial = self.fields['subject'].queryset.first()
            if self.fields['class_level'].queryset.count() == 1:
                self.fields['class_level'].initial = self.fields['class_level'].queryset.first()
        
        # Set default values
        if not self.instance.pk:  # Only for new exams
            self.fields['total_marks'].initial = 100
            self.fields['passing_marks'].initial = 40

class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ['marks_obtained', 'remarks']

class BulkResultForm(forms.Form):
    exam = forms.ModelChoiceField(queryset=Exam.objects.none())
    results_file = forms.FileField(
        label='Upload CSV File',
        help_text='Upload a CSV file with student marks. Format: student_id,marks_obtained,remarks'
    )
    
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        if self.teacher:
            self.fields['exam'].queryset = Exam.objects.filter(created_by=self.teacher)


# Add to forms.py

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'level_category', 'grade_level', 'capacity', 'code', 'class_teacher']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level_category': forms.Select(attrs={'class': 'form-control'}),
            'grade_level': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'class_teacher': forms.Select(attrs={'class': 'form-control'}),
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'credit_hours']  # Add credit_hours here
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'credit_hours': forms.NumberInput(attrs={  # Add this widget
                'class': 'form-control',
                'min': '1',
                'max': '10',
                'step': '1'
            }),
        }
        labels = {
            'name': 'Subject Name',
            'code': 'Subject Code',
            'description': 'Description',
            'credit_hours': 'Credit Hours',  # Add this label
        }

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'category', 'publisher', 'published_date', 'total_copies', 'available_copies']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'published_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class NoticeForm(forms.ModelForm):
    """Form for creating and editing notices"""
    class Meta:
        model = Notice
        fields = ['title', 'content', 'priority', 'target_audience', 'expiry_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notice title',
                'required': 'required'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter notice content',
                'required': 'required'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'target_audience': forms.Select(attrs={
                'class': 'form-control select2',
                'required': 'required'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'title': 'Notice Title *',
            'content': 'Content *',
            'priority': 'Priority Level',
            'target_audience': 'Target Audience *',
            'expiry_date': 'Expiry Date (Optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default priority
        if not self.instance.pk:
            self.initial['priority'] = 'MEDIUM'

class MessageForm(forms.ModelForm):
    """Form for sending messages"""
    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'content', 'file']
        widgets = {
            'receiver': forms.Select(attrs={
                'class': 'form-control select2',
                'required': 'required'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter message subject',
                'required': 'required'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter your message',
                'required': 'required'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'receiver': 'Recipient *',
            'subject': 'Subject *',
            'content': 'Message *',
            'file': 'Attachment (Optional)',
        }

class TimetableForm(forms.ModelForm):
    """Form for timetable management"""
    class Meta:
        model = Timetable
        fields = ['class_level', 'subject', 'teacher', 'day', 'start_time', 'end_time', 'room']
        widgets = {
            'class_level': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter room number'}),
        }

class AttendanceForm(forms.ModelForm):
    """Form for marking attendance"""
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter remarks (optional)'}),
        }

class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance marking"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'})
    )
    class_level = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )

class FeePaymentForm(forms.ModelForm):
    """Form for fee payments"""
    class Meta:
        model = FeePayment
        fields = ['fee', 'amount_paid', 'payment_date', 'payment_method', 'transaction_id', 'remarks']
        widgets = {
            'fee': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'required': 'required'
            }),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'payment_method': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter transaction ID'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter payment remarks'}),
        }

class TeacherPaymentForm(forms.ModelForm):
    """Form for teacher payments"""
    class Meta:
        model = TeacherPayment
        fields = ['teacher', 'amount', 'payment_date', 'payment_method', 'month', 'year', 'remarks']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'required': 'required'
            }),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'payment_method': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'month': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'required': 'required'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter payment remarks'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current year as default
        if not self.instance.pk:
            self.initial['year'] = timezone.now().year
            self.initial['month'] = timezone.now().month
            self.initial['payment_date'] = timezone.now().date()

class AcademicYearForm(forms.ModelForm):
    """Form for academic year management"""
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024-2025'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SectionForm(forms.ModelForm):
    """Form for section management"""
    class Meta:
        model = Section
        fields = ['name', 'class_name', 'capacity', 'room_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., A, B, C'}),
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter room number'}),
        }

class BookBorrowForm(forms.ModelForm):
    """Form for borrowing books"""
    class Meta:
        model = BookBorrowing
        fields = ['book', 'borrower', 'due_date']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'borrower': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default due date to 14 days from now
        if not self.instance.pk:
            self.initial['due_date'] = timezone.now().date() + timezone.timedelta(days=14)

class TransportRouteForm(forms.ModelForm):
    """Form for transport routes"""
    class Meta:
        model = TransportRoute
        fields = ['name', 'description', 'start_point', 'end_point', 'distance', 'fare']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter route name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter route description'}),
            'start_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter start point'}),
            'end_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter end point'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Distance in km'}),
            'fare': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter fare amount'}),
        }

class VehicleForm(forms.ModelForm):
    """Form for vehicle management"""
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'model', 'capacity', 'driver_name', 'driver_phone', 'insurance_expiry', 'status']
        widgets = {
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vehicle number'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vehicle model'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Enter seating capacity'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter driver name'}),
            'driver_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter driver phone'}),
            'insurance_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class HostelRoomForm(forms.ModelForm):
    """Form for hostel room management"""
    class Meta:
        model = HostelRoom
        fields = ['room_number', 'hostel', 'capacity', 'room_type', 'cost_per_student', 'facilities', 'status']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter room number'}),
            'hostel': forms.Select(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'cost_per_student': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List room facilities'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class HostelAllocationForm(forms.ModelForm):
    """Form for hostel allocation"""
    class Meta:
        model = HostelAllocation
        fields = ['student', 'room', 'allocated_date', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'room': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'allocated_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'status': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial['allocated_date'] = timezone.now().date()
            self.initial['status'] = 'ACTIVE'

class GradingSystemForm(forms.ModelForm):
    """Form for grading system management"""
    class Meta:
        model = GradingSystem
        fields = ['name', 'min_mark', 'max_mark', 'grade', 'points', 'remarks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter grade name'}),
            'min_mark': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'max_mark': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., A, B, C'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Excellent, Good'}),
        }

class PromotionForm(forms.Form):
    """Form for student promotion"""
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2', 'required': 'required'})
    )
    new_class = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    new_section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )

class UserProfileForm(forms.ModelForm):
    """Form for user profile updates"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class PasswordChangeForm(forms.Form):
    """Form for password change"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter current password'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords don't match.")

        return cleaned_data

class ReminderForm(forms.ModelForm):
    """Form for fee reminders"""
    class Meta:
        model = Reminder
        fields = ['fee', 'student_name', 'fee_type', 'sent_via', 'status', 'notes']
        widgets = {
            'fee': forms.Select(attrs={'class': 'form-control'}),
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'fee_type': forms.TextInput(attrs={'class': 'form-control'}),
            'sent_via': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BulkFeeForm(forms.Form):
    """Form for bulk fee creation"""
    class_level = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    fee_type = forms.ChoiceField(
        choices=Fee.FEE_TYPES,
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'required': 'required'
        })
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'})
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter fee description'})
    )

class StudentSearchForm(forms.Form):
    """Form for student search"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, ID, roll number...'
        })
    )
    class_filter = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status_filter = forms.ChoiceField(
        choices=[('', 'All Status'), ('active', 'Active'), ('inactive', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class TeacherSearchForm(forms.Form):
    """Form for teacher search"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, ID, qualification...'
        })
    )
    subject_filter = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status_filter = forms.ChoiceField(
        choices=[('', 'All Status'), ('active', 'Active'), ('inactive', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ParentSearchForm(forms.Form):
    """Form for parent search"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, phone...'
        })
    )

# Custom form for AJAX file uploads
class FileUploadForm(forms.Form):
    """Generic file upload form for AJAX requests"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png,.pdf,.doc,.docx,.xls,.xlsx'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'File description (optional)'
        })
    )

# Form for student-parent linking
class LinkStudentParentForm(forms.Form):
    """Form for linking students to parents"""
    parent = forms.ModelChoiceField(
        queryset=Parent.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2', 'required': 'required'})
    )

# Form for teacher class assignment
class AssignTeacherClassesForm(forms.Form):
    """Form for assigning classes to teachers"""
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2', 'required': 'required'})
    )

# Form for bulk operations
class BulkOperationForm(forms.Form):
    """Base form for bulk operations"""
    action = forms.ChoiceField(
        choices=[
            ('', 'Select Action'),
            ('delete', 'Delete Selected'),
            ('activate', 'Activate Selected'),
            ('deactivate', 'Deactivate Selected'),
            ('export', 'Export Selected')
        ],
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    object_ids = forms.CharField(
        widget=forms.HiddenInput()
    )

# If these models exist, add their forms too

class LibraryTransactionForm(forms.ModelForm):
    """Form for library transactions"""
    class Meta:
        model = LibraryTransaction
        fields = ['book', 'member', 'transaction_type', 'due_date', 'remarks']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-control'}),
            'member': forms.Select(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InventoryItemForm(forms.ModelForm):
    """Form for inventory items"""
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'quantity', 'unit_price', 'minimum_stock', 'location', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EventForm(forms.ModelForm):
    """Form for events and calendar"""
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_date', 'end_date', 'event_type', 'location', 'target_audience']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'target_audience': forms.Select(attrs={'class': 'form-control'}),
        }