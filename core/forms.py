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