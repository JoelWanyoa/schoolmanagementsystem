# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Count, Sum, Q,  Avg, Max, Min, StdDev
from django.db.models.functions import Coalesce
from django.db.models import FloatField, ExpressionWrapper
from core.models import *
from django.http import HttpResponse
import csv
from core.forms import *
import xlwt #For Excel Export
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import traceback
import json
from django.core.paginator import Paginator
import random
import string
from core.consumer import check_user_online
from core.timetabling.generator import TimetableGenerator, AdvancedTimetableGenerator

from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied

from django.core.mail import send_mail
from django.template.loader import render_to_string

from core.decorator import login_required_custom
import mimetypes

import calendar
from django.utils.html import strip_tags

from core.utils import (
    check_user_online,
    get_parent_children,
    calculate_exam_positions,
    get_conversations,
    get_user_type,
    generate_student_id,
    generate_teacher_id,
    send_fee_reminder_email
)
from core.utils import render_template_to_pdf
from django.utils import timezone
import csv
from openpyxl import Workbook

from core.access_control import admin_required, teacher_required, student_required, parent_required

# Add these to your existing imports section
import csv
import io
from io import BytesIO, StringIO
from decimal import Decimal, InvalidOperation

from core.decorators import teacher_required, student_required, parent_required
# For Excel export
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# For PDF export
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def export_payments(request):
    """Export payments to Excel"""
    # Get filter parameters
    teacher_id = request.GET.get('teacher', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    payment_method = request.GET.get('payment_method', '')
    
    # Filter payments
    payments = TeacherPayment.objects.all().select_related('teacher', 'processed_by')
    
    if teacher_id:
        payments = payments.filter(teacher_id=teacher_id)
    if month:
        payments = payments.filter(month=int(month))
    if year:
        payments = payments.filter(year=int(year))
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    # Create Excel workbook
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="teacher_payments_{timezone.now().strftime("%Y%m%d_%H%M")}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Payments')
    
    # Column headers
    headers = ['ID', 'Payment Date', 'Teacher', 'Teacher ID', 'Amount', 'Month', 'Year', 
               'Payment Method', 'Transaction ID', 'Remarks', 'Processed By', 'Processed Date']
    
    # Style for headers
    header_style = xlwt.easyxf(
        'font: bold on; align: horiz center; pattern: pattern solid, fore_colour light_green;'
    )
    
    # Write headers
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, header_style)
        ws.col(col_num).width = 4000  # Set column width
    
    # Style for data rows
    date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD')
    datetime_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:MM')
    amount_style = xlwt.easyxf(num_format_str='#,##0.00')
    
    # Write data
    for row_num, payment in enumerate(payments, 1):
        ws.write(row_num, 0, payment.id)
        ws.write(row_num, 1, payment.payment_date, date_style)
        ws.write(row_num, 2, payment.teacher.full_name)
        ws.write(row_num, 3, payment.teacher.teacher_id)
        ws.write(row_num, 4, float(payment.amount), amount_style)
        ws.write(row_num, 5, payment.month)
        ws.write(row_num, 6, payment.year)
        ws.write(row_num, 7, payment.get_payment_method_display())
        ws.write(row_num, 8, payment.transaction_id or '')
        ws.write(row_num, 9, payment.remarks or '')
        ws.write(row_num, 10, payment.processed_by.get_full_name())
        ws.write(row_num, 11, payment.created_at, datetime_style)
    
    # Add summary sheet
    ws2 = wb.add_sheet('Summary')
    ws2.write(0, 0, 'Payment Summary Report')
    ws2.write(1, 0, f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M")}')
    ws2.write(2, 0, f'Total Payments: {payments.count()}')
    ws2.write(3, 0, f'Total Amount: KSh {payments.aggregate(Sum("amount"))["amount__sum"] or 0:,.2f}')
    
    # Auto-size summary sheet columns
    ws2.col(0).width = 8000
    
    wb.save(response)
    return response

# def check_user_online(user):
#     """
#     Check if user is online by checking the is_online field
#     """
#     try:
#         # Check if user has is_online field
#         if hasattr(user, 'is_online'):
#             return bool(user.is_online)
        
#         # Check user profiles
#         if hasattr(user, 'student') and hasattr(user.student, 'is_online'):
#             return bool(user.student.is_online)
#         elif hasattr(user, 'teacher') and hasattr(user.teacher, 'is_online'):
#             return bool(user.teacher.is_online)
#         elif hasattr(user, 'parent') and hasattr(user.parent, 'is_online'):
#             return bool(user.parent.is_online)
        
#         return False
        
#     except Exception as e:
#         print(f"DEBUG: Error checking online status: {e}")
#         return False
def permission_denied(request):
    return render(request, 'permission_denied.html', status=403)

@admin_required
def initial_setup(request):
    """Initial setup page for first-time admin"""
    classes = Class.objects.all()
    sections = Section.objects.all()
    academic_years = AcademicYear.objects.all()
    
    context = {
        'classes': classes,
        'sections': sections,
        'academic_years': academic_years,
        'classes_exist': classes.exists(),
        'sections_exist': sections.exists(),
        'academic_years_exist': academic_years.exists(),
    }
    return render(request, 'setup/initial_setup.html', context)


@csrf_exempt
def create_admin_api(request):
    """API endpoint to create admin users (for development only)"""
    
    # Security check - only allow in DEBUG mode
    from django.conf import settings
    if not settings.DEBUG:
        return JsonResponse({'error': 'This endpoint is only available in debug mode'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Required fields
            username = data.get('username', 'admin')
            email = data.get('email', 'admin@example.com')
            password = data.get('password', 'admin123')
            
            # Check if user exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'User already exists'}, status=400)
            
            # Create admin user
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            return JsonResponse({
                'message': 'Admin user created successfully',
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'is_superuser': user.is_superuser
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
    
@admin_required
@csrf_exempt
def create_initial_classes(request):
    """Create initial classes for Kenyan system"""
    if request.method == 'POST':
        try:
            # ECDE Classes
            ecde_classes = [
                {'name': 'PP1', 'level_category': 'ECDE', 'grade_level': 'PP1', 'capacity': 25},
                {'name': 'PP2', 'level_category': 'ECDE', 'grade_level': 'PP2', 'capacity': 25},
            ]
            
            # Primary Classes
            primary_classes = [
                {'name': 'Grade 1', 'level_category': 'PRIMARY', 'grade_level': '1', 'capacity': 30},
                {'name': 'Grade 2', 'level_category': 'PRIMARY', 'grade_level': '2', 'capacity': 30},
                {'name': 'Grade 3', 'level_category': 'PRIMARY', 'grade_level': '3', 'capacity': 30},
                {'name': 'Grade 4', 'level_category': 'PRIMARY', 'grade_level': '4', 'capacity': 30},
                {'name': 'Grade 5', 'level_category': 'PRIMARY', 'grade_level': '5', 'capacity': 30},
                {'name': 'Grade 6', 'level_category': 'PRIMARY', 'grade_level': '6', 'capacity': 30},
            ]
            
            # Junior Secondary Classes
            junior_secondary_classes = [
                {'name': 'Grade 7', 'level_category': 'JUNIOR_SECONDARY', 'grade_level': '7', 'capacity': 35},
                {'name': 'Grade 8', 'level_category': 'JUNIOR_SECONDARY', 'grade_level': '8', 'capacity': 35},
                {'name': 'Grade 9', 'level_category': 'JUNIOR_SECONDARY', 'grade_level': '9', 'capacity': 35},
            ]
            
            all_classes = ecde_classes + primary_classes + junior_secondary_classes
            created_count = 0
            
            for class_data in all_classes:
                class_obj, created = Class.objects.get_or_create(
                    name=class_data['name'],
                    defaults={
                        'level_category': class_data['level_category'],
                        'grade_level': class_data['grade_level'],
                        'capacity': class_data['capacity'],
                        'code': f"{class_data['level_category']}_{class_data['grade_level']}"
                    }
                )
                if created:
                    created_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully created {created_count} classes!',
                'created_count': created_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating classes: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@admin_required
@csrf_exempt
def create_initial_sections(request):
    """Create sections for the first available class"""
    if request.method == 'POST':
        try:
            # Get the first class that exists
            first_class = Class.objects.first()
            
            if not first_class:
                return JsonResponse({
                    'success': False,
                    'message': 'Please create classes first before creating sections.'
                })
            
            section_names = ['A', 'B', 'C', 'D']
            created_count = 0
            
            for section_name in section_names:
                section, created = Section.objects.get_or_create(
                    name=section_name,
                    class_name=first_class,
                    defaults={'capacity': first_class.capacity}
                )
                if created:
                    created_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully created {created_count} sections for {first_class.name}!',
                'created_count': created_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating sections: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@admin_required
@csrf_exempt
def create_initial_academic_years(request):
    """Create initial academic years"""
    if request.method == 'POST':
        try:
            current_year = timezone.now().year
            academic_years = [
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
            
            created_count = 0
            for year_data in academic_years:
                year_obj, created = AcademicYear.objects.get_or_create(
                    name=year_data['name'],
                    defaults=year_data
                )
                if created:
                    created_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully created {created_count} academic years!',
                'created_count': created_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating academic years: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@admin_required
def complete_setup(request):
    """Mark setup as complete and redirect to dashboard"""
    # Check if all required data exists
    classes_exist = Class.objects.exists()
    sections_exist = Section.objects.exists()
    academic_years_exist = AcademicYear.objects.exists()
    
    if classes_exist and sections_exist and academic_years_exist:
        # Mark setup as complete
        settings = SystemSettings.get_instance()
        settings.setup_completed = True
        settings.save()
        
        messages.success(request, 'Initial setup completed successfully! You can now use the system.')
        return redirect('dashboard')  # Make sure this URL name exists in your urls.py
    else:
        missing_items = []
        if not classes_exist:
            missing_items.append("classes")
        if not sections_exist:
            missing_items.append("sections") 
        if not academic_years_exist:
            missing_items.append("academic years")
            
        messages.error(request, f'Please complete all setup steps. Missing: {", ".join(missing_items)}')
        return redirect('initial_setup')

@admin_required
def dashboard(request):
    try:
        # Get statistics
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.filter(is_active=True).count()
        total_classes = Class.objects.count()
        total_subjects = Subject.objects.count()
        
        # Recent notices
        recent_notices = Notice.objects.filter(is_active=True).order_by('-publish_date')[:5]
        
        # Today's attendance summary
        today = timezone.now().date()
        today_attendance = Attendance.objects.filter(date=today)
        present_today = today_attendance.filter(status=True).count()
        absent_today = today_attendance.filter(status=False).count()
        
        # Upcoming exams (next 30 days)
        thirty_days_later = today + timedelta(days=30)
        upcoming_exams = Exam.objects.filter(
            exam_date__gte=today,
            exam_date__lte=thirty_days_later
        ).order_by('exam_date')[:5]
        
        # Fee collection this month
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_fee_collection = FeePayment.objects.filter(
            payment_date__month=current_month,
            payment_date__year=current_year
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Format the fee collection to 2 decimal places
        monthly_fee_collection = float(monthly_fee_collection)
        
        # Pending admissions
        pending_admissions = AdmissionForm.objects.filter(status='PENDING').count()
        
        context = {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'total_subjects': total_subjects,
            'recent_notices': recent_notices,
            'present_today': present_today,
            'absent_today': absent_today,
            'upcoming_exams': upcoming_exams,
            'monthly_fee_collection': monthly_fee_collection,
            'pending_admissions': pending_admissions,
        }
        
        return render(request, 'dashboard/index.html', context)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Return basic context even if there are errors
        context = {
            'total_students': 0,
            'total_teachers': 0,
            'total_classes': 0,
            'total_subjects': 0,
            'recent_notices': [],
            'present_today': 0,
            'absent_today': 0,
            'upcoming_exams': [],
            'monthly_fee_collection': 0,
            'pending_admissions': 0,
        }
        return render(request, 'dashboard/index.html', context)

# Other users dashboards
@student_required
def student_dashboard(request):
    """Dashboard for students"""
    if not hasattr(request.user, 'student'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')

    try:
        student = request.user.student
        
        # Get student-specific data
        from django.utils import timezone
        from django.db.models import Q, Count, Sum
        from core.models import Attendance, Exam, ExamResult, Fee, AcademicYear
        
        today = timezone.now().date()
        
        # Today's attendance
        today_attendance = Attendance.objects.filter(
            student=student, 
            date=today
        ).first()
        
        # Upcoming exams (next 30 days)
        thirty_days_later = today + timezone.timedelta(days=30)
        upcoming_exams = Exam.objects.filter(
            class_level=student.current_class,
            exam_date__gte=today,
            exam_date__lte=thirty_days_later
        ).order_by('exam_date')[:5]
        
        # Recent results
        recent_results = ExamResult.objects.filter(
            student=student
        ).select_related('exam', 'exam__subject').order_by('-exam__exam_date')[:5]
        
        # Fee status with error handling
        # Fee status with error handling
        try:
            current_academic_year = AcademicYear.objects.filter(is_current=True).first()
            
            # Get all fees for the student
            fees = Fee.objects.filter(
                student=student,
                academic_year=current_academic_year
            )
            
            # Calculate totals based on your actual Fee model structure
            total_due = fees.aggregate(total=Sum('amount'))['total'] or 0
            
            # Option 1: If you have a status field
            paid_fees = fees.filter(status='paid')  # or whatever your paid status value is
            total_paid = paid_fees.aggregate(total=Sum('amount'))['total'] or 0
            
            # Option 2: If payments are tracked in a separate FeePayment model
            # total_paid = FeePayment.objects.filter(
            #     fee__student=student,
            #     fee__academic_year=current_academic_year
            # ).aggregate(total=Sum('amount'))['total'] or 0
            
            fee_status = {
                'total_due': total_due,
                'total_paid': total_paid,
                'pending_amount': total_due - total_paid
            }
            print(f"DEBUG: Fee status: {fee_status}")
        except Exception as e:
            print(f"DEBUG: Error getting fee status: {e}")
            fee_status = {'total_due': 0, 'total_paid': 0, 'pending_amount': 0}
        
        # Attendance summary
        attendance_summary = Attendance.objects.filter(student=student).aggregate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(status=True)),
            absent_days=Count('id', filter=Q(status=False))
        )
        
        context = {
            'student': student,
            'today_attendance': today_attendance,
            'upcoming_exams': upcoming_exams,
            'recent_results': recent_results,
            'fee_status': fee_status,
            'attendance_summary': attendance_summary,
        }
        
        return render(request, 'dashboard/student_dashboard.html', context)
        
    except Exception as e:
        print(f"Student dashboard error: {e}")
        messages.error(request, "Error loading student dashboard.")
        return render(request, 'dashboard/student_dashboard.html', {})

@student_required
def student_subjects(request):
    """View for student to see subjects allocated to their class and section"""
    try:
        student = request.user.student
        print(f"DEBUG: Loading subjects for {student.full_name}")
        print(f"DEBUG: Student class: {student.current_class}")
        print(f"DEBUG: Student section: {student.current_section}")
        
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        # Get subjects specifically for this student's class and section from timetable
        timetable_entries = Timetable.objects.filter(
            class_level=student.current_class,
            section=student.current_section
        ).select_related('subject', 'teacher').order_by('subject__name')
        
        # Create a list of unique subjects with their teachers
        subjects_data = []
        seen_subjects = set()
        
        for entry in timetable_entries:
            if entry.subject and entry.subject.id not in seen_subjects:
                subjects_data.append({
                    'subject': entry.subject,
                    'teacher': entry.teacher,
                })
                seen_subjects.add(entry.subject.id)
        
        print(f"DEBUG: Found {len(subjects_data)} subjects for {student.current_class} - {student.current_section}")
        for item in subjects_data:
            print(f"DEBUG: - {item['subject'].name} (Teacher: {item['teacher'].full_name if item['teacher'] else 'None'})")
        
        # If no subjects from timetable, show a message
        if not subjects_data:
            messages.info(request, "No subjects have been scheduled for your class yet. Please check back later.")
        
        # Calculate statistics
        core_count = len([s for s in subjects_data if s['subject'].category == 'CORE'])
        elective_count = len([s for s in subjects_data if s['subject'].category == 'ELECTIVE'])
        total_hours = sum([s['subject'].credit_hours for s in subjects_data])
        
        context = {
            'student': student,
            'class_subjects': subjects_data,
            'academic_year': current_academic_year,
            'core_subjects_count': core_count,
            'elective_subjects_count': elective_count,
            'total_credit_hours': total_hours,
        }
        
        return render(request, 'students/student_subjects.html', context)
        
    except Exception as e:
        print(f"DEBUG: Error in student_subjects: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
        student = getattr(request.user, 'student', None)
        messages.error(request, "Unable to load subjects at this time. Please try again later.")
        
        return render(request, 'students/student_subjects.html', {
            'student': student,
            'class_subjects': [],
            'core_subjects_count': 0,
            'elective_subjects_count': 0,
            'total_credit_hours': 0,
        })

@login_required
def subjects_by_class_section(request):
    """View to show all subjects organized by class and section"""
    classes = Class.objects.prefetch_related(
        'sections__section_subjects__subject',
        'sections__section_subjects__teacher'
    ).all()
    
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    context = {
        'classes': classes,
        'academic_year': current_academic_year,
    }
    return render(request, 'academic/subjects_by_class_section.html', context)

def get_subjects_by_class_section(class_level, section):
    """Get subjects for a specific class and section from timetable"""
    timetable_entries = Timetable.objects.filter(
        class_level=class_level,
        section=section
    ).select_related('subject', 'teacher').distinct()
    
    subjects_data = []
    for entry in timetable_entries:
        if entry.subject:
            subjects_data.append({
                'subject': entry.subject,
                'teacher': entry.teacher,
                'periods_per_week': Timetable.objects.filter(
                    class_level=class_level,
                    section=section,
                    subject=entry.subject
                ).count()
            })
    
    return subjects_data

@login_required
def class_section_subjects(request, class_id, section_id):
    """View to show subjects for a specific class and section"""
    class_level = get_object_or_404(Class, id=class_id)
    section = get_object_or_404(Section, id=section_id, class_name=class_level)
    
    subjects_data = get_subjects_by_class_section(class_level, section)
    
    context = {
        'class_level': class_level,
        'section': section,
        'subjects_data': subjects_data,
    }
    return render(request, 'academic/class_section_subjects.html', context)

from datetime import datetime, timedelta
from calendar import monthrange

@student_required
def student_attendance(request):
    """View for student to see their attendance"""
    try:
        student = request.user.student
        attendance_records = Attendance.objects.filter(student=student).order_by('-date')
        
        # Calculate summary
        total_days = attendance_records.count()
        present_days = attendance_records.filter(status=True).count()
        absent_days = attendance_records.filter(status=False).count()
        
        attendance_percentage = 0
        if total_days > 0:
            attendance_percentage = (present_days / total_days) * 100
        
        # Get current month and year
        today = timezone.now().date()
        current_month = today.strftime("%B %Y")
        year = today.year
        month = today.month
        
        # Get month filter from request (for previous months)
        selected_month = request.GET.get('month')
        selected_year = request.GET.get('year')
        
        if selected_month and selected_year:
            try:
                month = int(selected_month)
                year = int(selected_year)
                current_month = datetime(year, month, 1).strftime("%B %Y")
            except (ValueError, TypeError):
                month = today.month
                year = today.year
        
        # Get the number of days in the selected month
        _, num_days = monthrange(year, month)
        
        # Get first day of the month and its weekday (0=Monday, 6=Sunday)
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()  # 0=Monday, 6=Sunday
        
        # Week days starting from Monday
        week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Create calendar days with proper alignment and attendance data
        calendar_days = []
        
        # Add empty cells for days before the first day of the month
        for _ in range(first_weekday):
            calendar_days.append({'day': '', 'status': 'empty'})
        
        # Create a dictionary of attendance data for quick lookup for the selected month
        attendance_dict = {}
        month_attendance = attendance_records.filter(date__year=year, date__month=month)
        for record in month_attendance:
            attendance_dict[record.date.day] = record.status
        
        # Add actual days of the month with attendance status
        for day in range(1, num_days + 1):
            date_obj = datetime(year, month, day).date()
            if day in attendance_dict:
                status = 'present' if attendance_dict[day] else 'absent'
            else:
                # Check if it's a weekend (Saturday=5, Sunday=6)
                weekday = date_obj.weekday()
                if weekday >= 5:  # Saturday or Sunday
                    status = 'weekend'
                else:
                    status = 'no-data'
            
            calendar_days.append({
                'day': day,
                'status': status,
                'is_today': (day == today.day and month == today.month and year == today.year)
            })
        
        # Generate month navigation
        current_date = datetime(year, month, 1)
        prev_month = current_date - timedelta(days=1)
        next_month = current_date + timedelta(days=32)  # Add 32 days to ensure we go to next month
        
        # Only allow next month if it's not in the future
        next_month_allowed = (next_month.year < today.year) or (
            next_month.year == today.year and next_month.month <= today.month
        )
        
        # Get monthly statistics for dropdown
        monthly_stats = get_monthly_attendance_stats(attendance_records)
        
        context = {
            'student': student,
            'attendance_records': attendance_records,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'attendance_percentage': attendance_percentage,
            'current_month': current_month,
            'week_days': week_days,
            'calendar_days': calendar_days,
            'current_year': year,
            'current_month_num': month,
            'prev_month': prev_month.month,
            'prev_year': prev_month.year,
            'next_month': next_month.month,
            'next_year': next_month.year,
            'next_month_allowed': next_month_allowed,
            'monthly_stats': monthly_stats,
        }
        return render(request, 'students/student_attendance.html', context)
        
    except Exception as e:
        print(f"DEBUG: Error loading attendance: {e}")
        messages.error(request, "Error loading attendance. Please try again.")
        return render(request, 'students/student_attendance.html', {
            'student': getattr(request.user, 'student', None),
            'attendance_records': [],
            'total_days': 0,
            'present_days': 0,
            'absent_days': 0,
            'attendance_percentage': 0,
            'current_month': timezone.now().strftime("%B %Y"),
            'week_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'calendar_days': [],
        })

def get_monthly_attendance_stats(attendance_records):
    """Get attendance statistics grouped by month"""
    monthly_data = []
    
    # Get all unique year-month combinations from attendance records
    dates = attendance_records.dates('date', 'month')
    
    for date in dates:
        month_records = attendance_records.filter(
            date__year=date.year, 
            date__month=date.month
        )
        
        total = month_records.count()
        present = month_records.filter(status=True).count()
        percentage = (present / total * 100) if total > 0 else 0
        
        monthly_data.append({
            'year': date.year,
            'month': date.month,
            'month_name': date.strftime("%B %Y"),
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': percentage
        })
    
    return sorted(monthly_data, key=lambda x: (x['year'], x['month']), reverse=True)

@student_required
def student_results(request):
    """View for student to see their exam results"""
    student = request.user.student
    results = ExamResult.objects.filter(student=student).select_related('exam', 'exam__subject').order_by('-exam__exam_date')
    
    # Calculate summary stats
    total_passed = results.exclude(grade__in=['F', 'E']).count()
    
    avg_percentage = 0
    if results.exists():
        total_marks = 0
        total_possible = 0
        for r in results:
            total_marks += r.marks_obtained
            total_possible += r.exam.total_marks
        
        if total_possible > 0:
            avg_percentage = (total_marks / total_possible) * 100

    context = {
        'student': student,
        'results': results,
        'total_passed': total_passed,
        'avg_percentage': avg_percentage,
    }
    return render(request, 'students/student_results.html', context)

@student_required
def student_fee_status(request):
    """View for student to see their fee status"""
    student = request.user.student
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    fees = Fee.objects.filter(
        student=student,
        academic_year=current_academic_year
    ).order_by('due_date')
    
    total_due = fees.aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate total paid from all fee payments
    total_paid = FeePayment.objects.filter(
        student=student,
        fee__academic_year=current_academic_year
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    context = {
        'student': student,
        'fees': fees,
        'total_due': total_due,
        'total_paid': total_paid,
        'pending_amount': total_due - total_paid,
        'academic_year': current_academic_year,
    }
    return render(request, 'students/student_fee_status.html', context)

@student_required
def student_timetable(request):
    """View for student to see their class timetable"""
    try:
        student = request.user.student
        
        # Check if student has class and section assigned
        if not student.current_class:
            messages.warning(request, "You are not assigned to any class yet. Please contact the administrator.")
            return render(request, 'students/student_timetable.html', {
                'student': student,
                'no_class': True
            })
            
        # Get timetable for student's class and section
        # Filter by class first, then optional section to be safer
        filters = {'class_level': student.current_class}
        if student.current_section:
            filters['section'] = student.current_section
            
        timetable_entries = Timetable.objects.filter(
            **filters
        ).select_related('subject', 'teacher').order_by('day', 'period_number')
        
        # Group by day for better display
        days_order = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
        timetable_by_day = {}
        
        for day in days_order:
            day_entries = timetable_entries.filter(day=day)
            timetable_by_day[day] = day_entries
            
        # Get unique period numbers from current entries ordered by start time
        period_data = timetable_entries.values('period_number', 'start_time').distinct().order_by('start_time')
        period_nums = [p['period_number'] for p in period_data]
        
        # Ensure we have at least 1-8 if the list is empty
        if not period_nums:
            period_nums = range(1, 9)
        
        # Get current day for highlighting
        from datetime import datetime
        current_day = datetime.now().strftime('%A').upper()
        
        context = {
            'student': student,
            'timetable_entries': timetable_entries,
            'timetable_by_day': timetable_by_day,
            'days_order': days_order,
            'current_day': current_day,
            'period_nums': period_nums,
        }
        
        return render(request, 'students/student_timetable.html', context)
        
    except Exception as e:
        print(f"ERROR: student_timetable: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error loading timetable: {str(e)}")
        return render(request, 'students/student_timetable.html', {
            'student': getattr(request.user, 'student', None) if hasattr(request.user, 'student') else None,
            'error': True
        })
        
@student_required
def student_payment_history(request):
    """View for student to see their payment history"""
    try:
        student = request.user.student
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        # Get payment history from FeePayment model
        payment_history = FeePayment.objects.filter(
            student=student
        ).select_related('fee', 'fee__academic_year').order_by('-payment_date')
        
        # Total paid globally
        total_paid = FeePayment.objects.filter(student=student).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Pending fees for this year
        pending_fees = Fee.objects.filter(
            student=student,
            academic_year=current_academic_year,
            status='unpaid'
        )
        total_pending = pending_fees.aggregate(total=Sum('amount'))['total'] or 0
        
        context = {
            'student': student,
            'payment_history': payment_history,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'pending_fees': pending_fees,
            'academic_year': current_academic_year,
        }
        
        return render(request, 'students/student_payment_history.html', context)
        
    except Exception as e:
        print(f"DEBUG: Error loading payment history: {e}")
        messages.error(request, "Error loading payment history. Please try again.")
        return render(request, 'students/student_payment_history.html', {
            'student': getattr(request.user, 'student', None),
            'payment_history': [],
            'total_paid': 0,
        })

@student_required
def student_borrowed_books(request):
    """View for student to see their borrowed books"""
    try:
        student = request.user.student
        
        # Get borrowed books for the student (using BookBorrowing model)
        borrowed_books = BookBorrowing.objects.filter(
            borrower=request.user
        ).select_related('book').order_by('-borrowed_date')
        
        # Calculate overdue books
        today = timezone.now().date()
        for borrowing in borrowed_books:
            borrowing.is_overdue_bool = borrowing.is_overdue
            borrowing.overdue_days_count = borrowing.days_overdue if borrowing.is_overdue else 0
        
        context = {
            'student': student,
            'borrowed_books': borrowed_books,
            'today': today,
        }
        
        return render(request, 'students/student_borrowed_books.html', context)
        
    except Exception as e:
        print(f"DEBUG: Error loading borrowed books: {e}")
        messages.error(request, "Error loading borrowed books. Please try again.")
        return render(request, 'students/student_borrowed_books.html', {
            'student': getattr(request.user, 'student', None),
            'borrowed_books': [],
        })

@student_required
def student_borrow_book(request, book_id):
    """Allow a student to borrow a book directly"""
    try:
        book = get_object_or_404(Book, id=book_id)
        student = request.user.student
        
        # Check if student already has this book borrowed and active
        existing_borrowing = BookBorrowing.objects.filter(
            borrower=request.user,
            book=book,
            status='BORROWED'
        ).exists()
        
        if existing_borrowing:
            messages.warning(request, f"You already have an active borrowing for '{book.title}'.")
            return redirect('book_detail', book_id=book.id)

        if book.available_copies <= 0:
            messages.error(request, f"Sorry, no copies of '{book.title}' are currently available.")
            return redirect('book_detail', book_id=book.id)
            
        # Create borrowing record - default 14 days
        due_date = timezone.now() + timedelta(days=14)
        
        borrowing = BookBorrowing.objects.create(
            book=book,
            borrower=request.user,
            borrowed_date=timezone.now(),
            due_date=due_date,
            status='BORROWED'
        )
        
        # Update available copies
        book.available_copies -= 1
        book.save()
        
        messages.success(request, f"You have successfully borrowed '{book.title}'. Please return it by {due_date.strftime('%B %d, %Y')}.")
        return redirect('student_borrowed_books')
        
    except Exception as e:
        print(f"DEBUG: Error in student_borrow_book: {e}")
        messages.error(request, "An error occurred while trying to borrow the book.")
        return redirect('all_books')

@student_required
def student_assignments(request):
    """View for student to see their assignments"""
    try:
        student = request.user.student
        today = timezone.now().date()
        
        # Get assignments for student's class
        assignments = Assignment.objects.filter(
            class_level=student.current_class
        ).select_related('subject', 'teacher').order_by('-due_date')
        
        # Separate into upcoming and past assignments
        upcoming_assignments = assignments.filter(due_date__gte=today)
        past_assignments = assignments.filter(due_date__lt=today)
        
        # Get submissions if you have an AssignmentSubmission model
        submissions = {}
        if hasattr(student, 'assignmentsubmission_set'):
            submission_list = student.assignmentsubmission_set.all()
            for submission in submission_list:
                submissions[submission.assignment_id] = submission
        
        context = {
            'student': student,
            'upcoming_assignments': upcoming_assignments,
            'past_assignments': past_assignments,
            'submissions': submissions,
            'today': today,
            'submission_form': AssignmentSubmissionForm(),
        }
        
        return render(request, 'students/student_assignments.html', context)
        
    except Exception as e:
        print(f"DEBUG: Error loading assignments: {e}")
        messages.error(request, "Error loading assignments. Please try again.")
        return render(request, 'students/student_assignments.html', {
            'student': getattr(request.user, 'student', None),
            'upcoming_assignments': [],
            'past_assignments': [],
            'submissions': {},
            'submission_form': AssignmentSubmissionForm(),
        })

@student_required
@require_POST
def submit_assignment(request, assignment_id):
    """View to handle assignment submission"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user.student
    
    # Check if assignment is for student's class
    if assignment.class_level != student.current_class:
        messages.error(request, "You are not authorized to submit this assignment.")
        return redirect('student_assignments')
    
    # Check if already submitted
    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=student
    )
    
    form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
    if form.is_valid():
        submission = form.save(commit=False)
        submission.submitted = True
        submission.submitted_at = timezone.now()
        submission.save()
        messages.success(request, f"Assignment '{assignment.title}' submitted successfully!")
    else:
        messages.error(request, "Error submitting assignment. Please check your inputs.")
        
    return redirect('student_assignments')

@teacher_required
def grade_submission(request, submission_id):
    """View to handle grading of a submission"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    teacher = request.user.teacher
    
    # Ensure teacher owns the assignment
    if submission.assignment.teacher != teacher:
        messages.error(request, "You are not authorized to grade this submission.")
        return redirect('teacher_assignments')
    
    if request.method == 'POST':
        marks = request.POST.get('marks')
        feedback = request.POST.get('feedback')
        
        try:
            submission.marks_obtained = marks
            submission.feedback = feedback
            submission.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Grade updated successfully!'})
            
            messages.success(request, "Submission graded successfully!")
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
            messages.error(request, f"Error grading submission: {e}")
            
    return redirect('assignment_detail', assignment_id=submission.assignment.id)



@teacher_required
def teacher_dashboard(request):
    """Dashboard for teachers"""
    # Ensure only teachers can access this
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    try:
        teacher = request.user.teacher
        today = timezone.now().date()
        
        print(f"DEBUG: Loading dashboard for teacher: {teacher.full_name}")
        
        # Get teacher's classes (as class teacher)
        teacher_classes = Class.objects.filter(class_teacher=teacher)
        teacher_subjects = teacher.subjects.all()
        
        print(f"DEBUG: Teacher classes count: {teacher_classes.count()}")
        print(f"DEBUG: Teacher subjects count: {teacher_subjects.count()}")
        
        # If teacher has no classes assigned, show all classes for demo
        if not teacher_classes.exists():
            teacher_classes = Class.objects.all()[:3]  # Show first 3 classes for demo
            print(f"DEBUG: No classes assigned, showing demo classes: {teacher_classes.count()}")
        
        # Students in teacher's classes
        total_students = Student.objects.filter(
            current_class__in=teacher_classes,
            is_active=True
        ).count()
        
        print(f"DEBUG: Total students in teacher's classes: {total_students}")
        
        # Today's schedule - simplified approach
        today_schedule = []
        # For demo purposes, create a simple schedule
        if teacher_classes.exists():
            for i, class_obj in enumerate(teacher_classes[:3]):  # Show max 3 classes for demo
                today_schedule.append({
                    'class_level': class_obj,
                    'subject': teacher_subjects.first() if teacher_subjects.exists() else None,
                    'start_time': timezone.now().replace(hour=8+i, minute=0, second=0, microsecond=0),
                    'end_time': timezone.now().replace(hour=9+i, minute=0, second=0, microsecond=0),
                    'room_number': f"Room {i+1}",
                    'is_active': True
                })
        
        # Today's attendance
        today_attendance = Attendance.objects.filter(
            student__current_class__in=teacher_classes,
            date=today
        )
        present_today = today_attendance.filter(status=True).count()
        absent_today = today_attendance.filter(status=False).count()
        
        print(f"DEBUG: Attendance - Present: {present_today}, Absent: {absent_today}")
        
        # Assignments to grade - simplified
        assignments_to_grade = 5  # Demo value
        
        # Recent notices
        recent_notices = Notice.objects.filter(
            Q(target_audience='ALL') | Q(target_audience='TEACHERS'),
            is_active=True
        ).order_by('-publish_date')[:5]
        
        context = {
            'teacher': teacher,
            'teacher_classes': teacher_classes,
            'today_schedule': today_schedule,
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'assignments_to_grade': assignments_to_grade,
            'recent_notices': recent_notices,
            'total_subjects': teacher_subjects.count(),
        }
        
        print(f"DEBUG: Final context - Students: {total_students}, Classes: {teacher_classes.count()}")
        
        return render(request, 'dashboard/teacher_dashboard.html', context)
        
    except Exception as e:
        print(f"Teacher dashboard error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return basic context even if there are errors
        context = {
            'teacher': getattr(request.user, 'teacher', None),
            'teacher_classes': [],
            'today_schedule': [],
            'total_students': 0,
            'present_today': 0,
            'absent_today': 0,
            'assignments_to_grade': 0,
            'recent_notices': [],
            'total_subjects': 0,
        }
        return render(request, 'dashboard/teacher_dashboard.html', context)

@teacher_required
def teacher_my_classes(request):
    """View for teacher to see classes they teach"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
    }
    return render(request, 'teachers/my_classes.html', context)

@teacher_required
def teacher_class_schedule(request):
    """View for teacher's class schedule"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    today = timezone.now().date()
    
    # Get timetable for teacher's classes
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    # For demo purposes, create a sample schedule
    # In a real application, you'd have a Timetable model
    sample_schedule = []
    if teacher_classes.exists():
        for i, class_obj in enumerate(teacher_classes[:5]):  # Show max 5 classes
            sample_schedule.append({
                'class_level': class_obj,
                'subject': teacher.subjects.first() if teacher.subjects.exists() else None,
                'day': 'Monday',
                'start_time': timezone.now().replace(hour=8+i, minute=0, second=0, microsecond=0),
                'end_time': timezone.now().replace(hour=9+i, minute=0, second=0, microsecond=0),
                'room': f"Room {i+1}",
            })
    
    context = {
        'teacher': teacher,
        'schedule': sample_schedule,
        'today': today,
    }
    return render(request, 'teachers/class_schedule.html', context)

def class_subjects_management(request, class_id):
    """View to manage subjects for a specific class"""
    class_obj = get_object_or_404(Class, id=class_id)
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get timetable entries with teacher information
    timetable_entries = Timetable.objects.filter(
        class_level=class_obj
    ).select_related('subject', 'teacher').order_by('subject__name')
    
    # Create a list of unique subjects with their timetable information
    current_subjects_data = []
    seen_subjects = set()
    
    for entry in timetable_entries:
        if entry.subject and entry.subject.id not in seen_subjects:
            current_subjects_data.append({
                'subject': entry.subject,
                'teacher': entry.teacher,
                'section': entry.section,
                'day': entry.day,
                'period': entry.period_number,
            })
            seen_subjects.add(entry.subject.id)
    
    # If no subjects from timetable, check assignments as fallback
    if not current_subjects_data:
        assignment_subjects = Subject.objects.filter(
            assignment__class_level=class_obj
        ).distinct()
        for subject in assignment_subjects:
            current_subjects_data.append({
                'subject': subject,
                'teacher': None,
                'section': None,
                'day': None,
                'period': None,
            })
    
    all_subjects = Subject.objects.all()
    teachers = Teacher.objects.all()
    sections = class_obj.section_set.all()
    
    # Form data for dropdowns
    days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    period_numbers = range(1, 9)  # 8 periods per day
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher')
        section_id = request.POST.get('section')
        day = request.POST.get('day')
        period_number = request.POST.get('period_number')
        
        if subject_id and section_id and day and period_number:
            subject = get_object_or_404(Subject, id=subject_id)
            teacher = get_object_or_404(Teacher, id=teacher_id) if teacher_id else None
            section = get_object_or_404(Section, id=section_id)
            
            try:
                # Check if this timeslot is already occupied
                existing_entry = Timetable.objects.filter(
                    class_level=class_obj,
                    section=section,
                    day=day,
                    period_number=period_number
                ).first()
                
                if existing_entry:
                    messages.warning(request, f"This timeslot is already occupied by {existing_entry.subject.name}. Please choose a different time.")
                else:
                    # Create a new timetable entry
                    Timetable.objects.create(
                        class_level=class_obj,
                        section=section,
                        subject=subject,
                        teacher=teacher,
                        day=day,
                        period_number=period_number,
                        start_time='08:00:00',
                        end_time='09:00:00',
                        room=class_obj.name
                    )
                    messages.success(request, f"Subject '{subject.name}' has been added to {class_obj.name}")
                    return redirect('class_subjects_management', class_id=class_id)
                    
            except Exception as e:
                messages.error(request, f"Error adding subject: {str(e)}")
        else:
            messages.error(request, "Please fill all required fields.")
    
    context = {
        'class_obj': class_obj,
        'current_subjects': current_subjects_data,  # Use the structured data
        'all_subjects': all_subjects,
        'teachers': teachers,
        'sections': sections,
        'days': days,
        'period_numbers': period_numbers,
        'academic_year': current_academic_year,
    }
    return render(request, 'academic/class_subjects_management.html', context)

@teacher_required
def teacher_my_students(request):
    """View for teacher to see students in their classes"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    # Get students from teacher's classes
    students = Student.objects.filter(
        current_class__in=teacher_classes,
        is_active=True
    ).select_related('current_class', 'current_section').order_by('current_class__name', 'roll_number')
    
    # Filter by class if specified
    class_filter = request.GET.get('class')
    if class_filter:
        students = students.filter(current_class_id=class_filter)
    
    context = {
        'teacher': teacher,
        'students': students,
        'teacher_classes': teacher_classes,
        'class_filter': class_filter,
    }
    return render(request, 'teachers/my_students.html', context)

@teacher_required
def teacher_attendance(request):
    # Check if user has a teacher profile
    if not hasattr(request.user, 'teacher'):
        messages.error(request, 'Teacher profile not found. Please contact administrator.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get the teacher's classes - FIXED: using class_teacher instead of teacher
            teacher_classes = Class.objects.filter(class_teacher=request.user.teacher)
            
            # Get all students from the teacher's classes
            students = Student.objects.filter(current_class__in=teacher_classes)
            
            for student in students:
                status_key = f'student_{student.id}'
                remarks_key = f'remarks_{student.id}'
                
                if status_key in request.POST:
                    status = request.POST.get(status_key) == 'present'
                    remarks = request.POST.get(remarks_key, '')
                    
                    # Use get_or_create to handle attendance
                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        date=attendance_date,
                        defaults={
                            'status': status,
                            'remarks': remarks,
                            'marked_by_id': request.user.id  # Use ID directly
                        }
                    )
                    
                    if not created:
                        attendance.status = status
                        attendance.remarks = remarks
                        attendance.marked_by_id = request.user.id
                        attendance.save()
            
            messages.success(request, 'Attendance marked successfully!')
            return redirect('teacher_attendance')
            
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
    
    # GET request handling
    today = timezone.now().date()
    selected_date = request.GET.get('date', today.isoformat())
    
    try:
        attendance_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        attendance_date = today
    
    # Get teacher's classes - FIXED: using class_teacher
    teacher_classes = Class.objects.filter(class_teacher=request.user.teacher)
    students = Student.objects.filter(current_class__in=teacher_classes)
    
    # Get today's attendance for the selected date
    today_attendance = Attendance.objects.filter(
        student__in=students,
        date=attendance_date
    )
    
    # Calculate counts
    present_count = today_attendance.filter(status=True).count()
    absent_count = today_attendance.filter(status=False).count()
    
    context = {
        'students': students,
        'today_attendance': today_attendance,
        'today': today,
        'selected_date': selected_date,
        'present_count': present_count,
        'absent_count': absent_count,
        'total_students': students.count(),
        'teacher_classes': teacher_classes,
    }
    
    return render(request, 'teachers/attendance.html', context)

@teacher_required
def teacher_subjects(request):
    """View for teacher to see subjects they teach"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    subjects = teacher.subjects.all()
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
    }
    return render(request, 'teachers/subjects.html', context)

@teacher_required
def teacher_assignments(request):
    """View for teacher to manage assignments"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    
    # Get assignments created by this teacher
    assignments = Assignment.objects.filter(teacher=teacher).select_related('subject', 'class_level')
    
    # Calculate statistics with safe defaults
    total_assignments = assignments.count()
    
    # Count assignments with pending grading
    pending_grading = 0
    for assignment in assignments:
        try:
            pending_grading += assignment.submissions.filter(
                submitted=True, 
                marks_obtained__isnull=True
            ).count()
        except:
            pass  # Handle case where submissions relationship doesn't exist yet
    
    # Total submissions across all assignments
    try:
        submitted_count = AssignmentSubmission.objects.filter(
            assignment__teacher=teacher,
            submitted=True
        ).count()
    except:
        submitted_count = 0
    
    # Overdue assignments
    overdue_count = assignments.filter(due_date__lt=timezone.now()).count()
    
    # Create sample assignments for demo if none exist
    if not assignments.exists():
        try:
            teacher_class = Class.objects.filter(class_teacher=teacher).first()
            teacher_subject = teacher.subjects.first()
            
            if teacher_class and teacher_subject:
                sample_assignments = [
                    {
                        'title': 'Mathematics Homework - Algebra Basics',
                        'subject': teacher_subject,
                        'class_level': teacher_class,
                        'assignment_type': 'HOMEWORK',
                        'total_marks': 100,
                        'due_date': timezone.now() + timedelta(days=7),
                        'status': 'PUBLISHED',
                        'teacher': teacher
                    },
                    {
                        'title': 'Science Project - Environmental Studies',
                        'subject': teacher_subject,
                        'class_level': teacher_class,
                        'assignment_type': 'PROJECT',
                        'total_marks': 100,
                        'due_date': timezone.now() + timedelta(days=14),
                        'status': 'PUBLISHED',
                        'teacher': teacher
                    }
                ]
                
                for assignment_data in sample_assignments:
                    Assignment.objects.create(**assignment_data)
                
                # Refresh the assignments queryset
                assignments = Assignment.objects.filter(teacher=teacher).select_related('subject', 'class_level')
        except Exception as e:
            print(f"Error creating sample assignments: {e}")
    
    # Pagination
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    assignments_page = paginator.get_page(page_number)
    
    context = {
        'teacher': teacher,
        'assignments': assignments_page,
        'teacher_classes': Class.objects.filter(class_teacher=teacher),
        'total_assignments': total_assignments,
        'pending_count': pending_grading,
        'submitted_count': submitted_count,
        'overdue_count': overdue_count,
        'now': timezone.now(),
    }
    return render(request, 'teachers/assignments.html', context)

@teacher_required
def class_teacher_timetable(request):
    """Timetable view for teachers - shows all classes where they are class teacher"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Access denied. Teacher profile not found.")
        return redirect('login')
    
    # Get all classes where this teacher is the class teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    # Get timetable entries for all these classes
    timetable_data = {}
    for class_obj in teacher_classes:
        timetable_entries = Timetable.objects.filter(
            class_level=class_obj
        ).select_related(
            'class_level', 'section', 'subject', 'teacher'
        ).order_by('day', 'period_number')
        
        timetable_data[class_obj] = timetable_entries
    
    # Get today's schedule for all classes
    today = timezone.now().date()
    today_schedule = Timetable.objects.filter(
        class_level__in=teacher_classes,
        day=today.strftime('%A').upper()
    ).select_related(
        'class_level', 'section', 'subject'
    ).order_by('start_time')
    
    # Define periods for timetable display
    periods = [
        {'number': 1, 'start_time': time(8, 0), 'end_time': time(8, 40)},
        {'number': 2, 'start_time': time(8, 40), 'end_time': time(9, 20)},
        {'number': 3, 'start_time': time(9, 20), 'end_time': time(10, 0)},
        {'number': 4, 'start_time': time(10, 20), 'end_time': time(11, 0)},  # After break
        {'number': 5, 'start_time': time(11, 0), 'end_time': time(11, 40)},
        {'number': 6, 'start_time': time(11, 40), 'end_time': time(12, 20)},
        {'number': 7, 'start_time': time(12, 20), 'end_time': time(13, 0)},
        {'number': 8, 'start_time': time(14, 0), 'end_time': time(14, 40)},  # After lunch
        {'number': 9, 'start_time': time(14, 40), 'end_time': time(15, 20)},
    ]
    
    days = [
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
    ]
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'timetable_data': timetable_data,
        'today_schedule': today_schedule,
        'today': today,
        'periods': periods,
        'days': days,
        'current_week': timezone.now().isocalendar()[1],
    }
    return render(request, 'teachers/class_schedule.html', context)

@teacher_required
def class_teacher_timetable_data(request):
    """Get timetable data for all classes where teacher is class teacher"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Teacher not found'}, status=403)
    
    # Get all classes where this teacher is class teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    # Get timetable entries for all these classes
    timetable_entries = Timetable.objects.filter(
        class_level__in=teacher_classes
    ).select_related(
        'class_level', 'section', 'subject', 'teacher'
    ).order_by('class_level', 'day', 'period_number')
    
    # Format data for response
    data = []
    for entry in timetable_entries:
        entry_data = {
            'id': entry.id,
            'class_level': {
                'id': entry.class_level.id,
                'name': entry.class_level.name,
                'code': entry.class_level.code
            },
            'section': {
                'id': entry.section.id,
                'name': entry.section.name
            },
            'subject': {
                'id': entry.subject.id if entry.subject else None,
                'name': entry.subject.name if entry.subject else 'No Subject',
                'code': entry.subject.code if entry.subject else ''
            },
            'teacher': {
                'id': entry.teacher.id if entry.teacher else None,
                'name': entry.teacher.full_name if entry.teacher else 'No Teacher'
            },
            'day': entry.day,
            'day_display': entry.get_day_display(),
            'period_number': entry.period_number,
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'room': entry.room,
            'is_break': entry.is_break,
            'break_name': entry.break_name,
        }
        data.append(entry_data)
    
    return JsonResponse({'data': data})

@teacher_required
def teacher_timetable(request):
    """Timetable view for teachers - shows only periods where THIS teacher is scheduled to teach"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Access denied. Teacher profile not found.")
        return redirect('login')
    
    # Get timetable entries where THIS teacher is assigned to teach
    timetable_entries = Timetable.objects.filter(
        teacher=teacher
    ).select_related(
        'class_level', 'section', 'subject'
    ).order_by('day', 'period_number')
    
    # Get today's schedule for this teacher
    today = timezone.now().date()
    today_day = today.strftime('%A').upper()
    today_schedule = timetable_entries.filter(day=today_day).order_by('start_time')
    
    # Get unique classes and subjects from the timetable entries
    teacher_classes = set()
    teacher_subjects = set()
    
    for entry in timetable_entries:
        if entry.class_level:
            teacher_classes.add(entry.class_level)
        if entry.subject:
            teacher_subjects.add(entry.subject)
    
    # Also include subjects assigned to teacher
    assigned_subjects = teacher.subjects.all()
    teacher_subjects.update(assigned_subjects)
    
    context = {
        'teacher': teacher,
        'timetable_entries': timetable_entries,
        'today_schedule': today_schedule,
        'today': today,
        'teacher_classes': list(teacher_classes),
        'teacher_subjects': list(teacher_subjects),
        'current_week': timezone.now().isocalendar()[1],
    }
    return render(request, 'teachers/teacher_timetable.html', context)

@teacher_required
def teacher_timetable_data(request):
    """Get timetable data for THIS teacher's teaching schedule"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Teacher not found'}, status=403)
    
    # Get timetable entries where THIS teacher is assigned to teach
    timetable_entries = Timetable.objects.filter(
        teacher=teacher
    ).select_related(
        'class_level', 'section', 'subject'
    ).order_by('day', 'period_number')
    
    # Format data for response
    data = []
    for entry in timetable_entries:
        entry_data = {
            'id': entry.id,
            'class_level': {
                'id': entry.class_level.id,
                'name': entry.class_level.name,
                'code': entry.class_level.code
            },
            'section': {
                'id': entry.section.id,
                'name': entry.section.name
            },
            'subject': {
                'id': entry.subject.id if entry.subject else None,
                'name': entry.subject.name if entry.subject else 'No Subject',
                'code': entry.subject.code if entry.subject else ''
            },
            'day': entry.day,
            'day_display': entry.get_day_display(),
            'period_number': entry.period_number,
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'room': entry.room,
            'is_break': entry.is_break,
            'break_name': entry.break_name,
        }
        data.append(entry_data)
    
    return JsonResponse({'data': data})

@teacher_required
def teacher_exam_results(request):
    """View for teacher to manage exam results"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    # Get exam results for teacher's classes - FIXED QUERYSET
    exam_results = ExamResult.objects.filter(
        student__current_class__in=teacher_classes
    ).select_related('student', 'exam', 'exam__subject').order_by('-exam__exam_date')
    
    # Alternative approach if the above doesn't work:
    # Get exams for teacher's classes first, then get results for those exams
    # exams_in_teacher_classes = Exam.objects.filter(class_level__in=teacher_classes)
    # exam_results = ExamResult.objects.filter(
    #     exam__in=exams_in_teacher_classes
    # ).select_related('student', 'exam', 'exam__subject').order_by('-exam__exam_date')
    
    # Filter by class or subject
    class_filter = request.GET.get('class')
    subject_filter = request.GET.get('subject')
    
    if class_filter:
        exam_results = exam_results.filter(student__current_class_id=class_filter)
    
    if subject_filter:
        exam_results = exam_results.filter(exam__subject_id=subject_filter)
    
    context = {
        'teacher': teacher,
        'exam_results': exam_results,
        'teacher_classes': teacher_classes,
        'subjects': teacher.subjects.all(),
        'class_filter': class_filter,
        'subject_filter': subject_filter,
    }
    return render(request, 'teachers/exam_results.html', context)

@teacher_required
def teacher_assignments(request):
    """View for teacher to manage assignments"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    assignments = Assignment.objects.filter(teacher=teacher).select_related('subject', 'class_level')
    
    # Calculate statistics
    total_assignments = assignments.count()
    pending_grading = assignments.filter(
        submissions__submitted=True,
        submissions__marks_obtained__isnull=True
    ).distinct().count()
    
    submitted_count = AssignmentSubmission.objects.filter(
        assignment__teacher=teacher,
        submitted=True
    ).count()
    
    overdue_count = assignments.filter(due_date__lt=timezone.now()).count()
    
    # Pagination
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    assignments_page = paginator.get_page(page_number)
    
    context = {
        'teacher': teacher,
        'assignments': assignments_page,
        'teacher_classes': Class.objects.filter(class_teacher=teacher),
        'total_assignments': total_assignments,
        'pending_count': pending_grading,
        'submitted_count': submitted_count,
        'overdue_count': overdue_count,
        'now': timezone.now(),
    }
    return render(request, 'teachers/assignments.html', context)

@teacher_required
def assignment_create(request):
    """Create a new assignment"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    
    # Check if teacher has subjects and classes assigned
    has_subjects = teacher.subjects.exists()
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    has_classes = teacher_classes.exists()
    
    if not has_subjects or not has_classes:
        messages.warning(request, 
            f"Cannot create assignment. You need to be assigned {'subjects' if not has_subjects else ''}{' and ' if not has_subjects and not has_classes else ''}{'classes' if not has_classes else ''}.")
        return redirect('teacher_assignments')
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            try:
                assignment = form.save(commit=False)
                assignment.teacher = teacher
                assignment.save()
                
                messages.success(request, f'Assignment "{assignment.title}" created successfully!')
                return redirect('assignment_detail', assignment_id=assignment.id)
                
            except Exception as e:
                messages.error(request, f'Error creating assignment: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm(teacher=teacher)
    
    context = {
        'form': form,
        'teacher': teacher,
        'teacher_classes': teacher_classes,
    }
    return render(request, 'teachers/assignment_form.html', context)

@teacher_required
def assignment_detail(request, assignment_id):
    """View assignment details and submissions"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
    
    # Get submissions for this assignment
    submissions = assignment.submissions.select_related('student').all()
    
    # Calculate submission statistics using real data only
    try:
        total_students = assignment.total_students
    except Exception as e:
        print(f"Error calculating total students: {e}")
        total_students = 0
    
    submitted_count = submissions.filter(submitted=True).count()
    graded_count = submissions.filter(marks_obtained__isnull=False).count()
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'teacher': teacher,
        'total_students': total_students,
        'submitted_count': submitted_count,
        'graded_count': graded_count,
    }
    return render(request, 'teachers/assignment_detail.html', context)

@teacher_required
def assignment_edit(request, assignment_id):
    """Edit an existing assignment"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment, teacher=teacher)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Assignment "{assignment.title}" updated successfully!')
                return redirect('assignment_detail', assignment_id=assignment.id)
            except Exception as e:
                messages.error(request, f'Error updating assignment: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm(instance=assignment, teacher=teacher)
    
    # Get all classes that the teacher can teach (including the current one)
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    if not teacher_classes.exists():
        # If teacher has no assigned classes, show all classes as fallback
        teacher_classes = Class.objects.all()
    
    context = {
        'form': form,
        'assignment': assignment,
        'teacher': teacher,
        'teacher_classes': teacher_classes,
    }
    return render(request, 'teachers/assignment_form.html', context)

@teacher_required
def assignment_delete(request, assignment_id):
    """Delete an assignment"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
    
    if request.method == 'POST':
        assignment_title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{assignment_title}" deleted successfully!')
        return redirect('teacher_assignments')
    
    context = {
        'assignment': assignment,
    }
    return render(request, 'teachers/assignment_confirm_delete.html', context)

@teacher_required
def assignment_download_submissions(request, assignment_id):
    """Download all submissions for an assignment as zip"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
    
    # Create a zip file with all submissions
    import zipfile
    from io import BytesIO
    
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for submission in assignment.submissions.filter(submitted=True):
            if submission.submission_file:
                file_name = f"{submission.student.roll_number}_{submission.student.last_name}_{submission.submission_file.name}"
                zip_file.write(submission.submission_file.path, file_name)
    
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{assignment.title}_submissions.zip"'
    return response

@teacher_required
def teacher_exam_management(request):
    """Main exam management dashboard for teachers"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    teacher_subjects = teacher.subjects.all()
    
    # Get statistics
    total_exams = Exam.objects.filter(created_by=request.user).count()
    exams_this_month = Exam.objects.filter(
        created_by=request.user,
        exam_date__month=timezone.now().month,
        exam_date__year=timezone.now().year
    ).count()
    
    # Recent exams
    recent_exams = Exam.objects.filter(created_by=request.user).order_by('-exam_date')[:5]
    
    # All exams
    all_exams = Exam.objects.filter(created_by=request.user).order_by('-exam_date')
    
    # Upcoming exams
    upcoming_exams = Exam.objects.filter(
        created_by=request.user,
        exam_date__gte=timezone.now().date()
    ).order_by('exam_date')[:5]
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'teacher_subjects': teacher_subjects,
        'all_exams': all_exams,
        'total_exams': total_exams,
        'exams_this_month': exams_this_month,
        'recent_exams': recent_exams,
        'upcoming_exams': upcoming_exams,
        'today': timezone.now().date(),
    }
    return render(request, 'teachers/exam_management.html', context)

@teacher_required
def create_exam(request):
    """Create a new exam"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    
    # Check if teacher has subjects and classes assigned
    has_subjects = teacher.subjects.exists()
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    has_classes = teacher_classes.exists()
    
    if not has_subjects or not has_classes:
        messages.warning(request, 
            f"Cannot create exam. You need to be assigned {'subjects' if not has_subjects else ''}{' and ' if not has_subjects and not has_classes else ''}{'classes' if not has_classes else ''}.")
        return redirect('teacher_exam_management')
    
    if request.method == 'POST':
        form = ExamForm(request.POST, teacher=teacher)
        if form.is_valid():
            try:
                exam = form.save(commit=False)
                exam.created_by = request.user
                exam.save()
                messages.success(request, f'Exam "{exam.name}" created successfully!')
                return redirect('enter_marks', exam_id=exam.id)
            except Exception as e:
                messages.error(request, f'Error creating exam: {str(e)}')
        else:
            # Debug form errors
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamForm(teacher=teacher)
    
    context = {
        'form': form,
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'title': 'Create New Exam'
    }
    return render(request, 'teachers/exam_form.html', context)

@login_required
def enter_marks(request, exam_id):
    """Enter marks for a specific exam - Prevent re-entry of marks"""
    if request.user.is_staff:
        exam = get_object_or_404(Exam, id=exam_id)
    else:
        if not hasattr(request.user, 'teacher'):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    # Get students in the exam class
    students = Student.objects.filter(
        current_class=exam.class_level,
        is_active=True
    ).order_by('roll_number')
    
    # Get existing results for pre-population
    existing_results = ExamResult.objects.filter(exam=exam)
    result_dict = {}
    for result in existing_results:
        result_dict[result.student.id] = result
    
    # Check if all students already have marks
    all_graded = len(result_dict) == students.count()
    
    if request.method == 'POST':
        # If all marks are already entered, prevent further changes
        if all_graded and not request.POST.get('force_update'):
            messages.warning(request, f'All marks for {exam.name} have already been entered. Use "Edit Marks" to make changes.')
            return redirect('exam_results', exam_id=exam.id)
        
        try:
            from decimal import Decimal, InvalidOperation
            updated_count = 0
            new_count = 0
            
            for student in students:
                marks_key = f'marks_{student.id}'
                remarks_key = f'remarks_{student.id}'
                
                if marks_key in request.POST:
                    marks_obtained = request.POST.get(marks_key)
                    remarks = request.POST.get(remarks_key, '')
                    
                    if marks_obtained:  # Only save if marks are provided
                        try:
                            # Convert to Decimal for proper storage
                            marks_decimal = Decimal(marks_obtained)
                            
                            # Validate marks are within range
                            if marks_decimal < 0:
                                messages.error(request, f'Marks cannot be negative for {student.full_name}')
                                continue
                            if marks_decimal > exam.total_marks:
                                messages.error(request, f'Marks cannot exceed total marks ({exam.total_marks}) for {student.full_name}')
                                continue
                            
                            # Check if result already exists
                            existing_result = result_dict.get(student.id)
                            
                            # Update or create exam result
                            result, created = ExamResult.objects.update_or_create(
                                exam=exam,
                                student=student,
                                defaults={
                                    'marks_obtained': marks_decimal,
                                    'remarks': remarks
                                }
                            )
                            
                            if created:
                                new_count += 1
                            else:
                                updated_count += 1
                            
                        except InvalidOperation:
                            messages.error(request, f'Invalid marks format for {student.full_name}')
                            continue
            
            # Calculate positions after saving all marks
            calculate_exam_positions(exam)
            
            if new_count > 0 and updated_count > 0:
                messages.success(request, f'Successfully added {new_count} new marks and updated {updated_count} existing marks for {exam.name}!')
            elif new_count > 0:
                messages.success(request, f'Successfully entered marks for {new_count} students in {exam.name}!')
            elif updated_count > 0:
                messages.success(request, f'Successfully updated marks for {updated_count} students in {exam.name}!')
            else:
                messages.info(request, 'No changes were made to the marks.')
                
            return redirect('exam_results', exam_id=exam.id)
            
        except Exception as e:
            messages.error(request, f'Error entering marks: {str(e)}')
    
    context = {
        'exam': exam,
        'students': students,
        'result_dict': result_dict,
        'all_graded': all_graded,
        'graded_count': len(result_dict),
        'total_students': students.count(),
    }
    return render(request, 'teachers/enter_marks.html', context)

def calculate_exam_positions(exam):
    """Calculate positions for an exam based on marks"""
    results = ExamResult.objects.filter(exam=exam).order_by('-marks_obtained')
    
    position = 1
    prev_marks = None
    same_rank_count = 0
    
    for result in results:
        # Convert Decimal to float for comparison
        current_marks = float(result.marks_obtained)
        
        if prev_marks is not None and current_marks == prev_marks:
            same_rank_count += 1
        else:
            position += same_rank_count
            same_rank_count = 1
        
        result.position = position
        result.save()
        prev_marks = current_marks

@teacher_required
def edit_marks(request, exam_id):
    """Edit existing marks for an exam"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    # Similar logic to enter_marks but always allows editing
    # You can reuse the same template with editing_mode=True
    
    context = {
        'exam': exam,
        'students': Student.objects.filter(current_class=exam.class_level, is_active=True),
        'result_dict': {r.student.id: r for r in ExamResult.objects.filter(exam=exam)},
        'editing_mode': True,
    }
    return render(request, 'teachers/enter_marks.html', context)

@login_required
def exam_results(request, exam_id):
    """View results for a specific exam"""
    if request.user.is_staff:
        exam = get_object_or_404(Exam, id=exam_id)
    else:
        if not hasattr(request.user, 'teacher'):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('position')
    
    # Calculate statistics
    total_students = results.count()
    if total_students > 0:
        average_marks = results.aggregate(Avg('marks_obtained'))['marks_obtained__avg']
        highest_marks = results.aggregate(Max('marks_obtained'))['marks_obtained__max']
        lowest_marks = results.aggregate(Min('marks_obtained'))['marks_obtained__min']
        
        # Grade distribution
        grade_distribution = results.values('grade').annotate(count=Count('id')).order_by('grade')
    else:
        average_marks = highest_marks = lowest_marks = 0
        grade_distribution = []
    
    context = {
        'exam': exam,
        'results': results,
        'teacher': teacher,
        'total_students': total_students,
        'average_marks': average_marks,
        'highest_marks': highest_marks,
        'lowest_marks': lowest_marks,
        'grade_distribution': grade_distribution,
    }
    return render(request, 'teachers/exam_results.html', context)

@login_required
def exam_analysis(request, exam_id):
    """Detailed analysis for an exam"""
    if request.user.is_staff:
        exam = get_object_or_404(Exam, id=exam_id)
    else:
        if not hasattr(request.user, 'teacher'):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    results = ExamResult.objects.filter(exam=exam).select_related('student')
    
    # Detailed statistics
    stats = results.aggregate(
        avg_marks=Avg('marks_obtained'),
        max_marks=Max('marks_obtained'),
        min_marks=Min('marks_obtained'),
        std_dev=StdDev('marks_obtained'),
        count=Count('id')
    )
    
    # Grade distribution
    grade_data = results.values('grade').annotate(
        count=Count('id'),
        percentage=ExpressionWrapper(
            Count('id') * 100.0 / stats['count'],
            output_field=FloatField()
        )
    ).order_by('grade')
    
    # Marks distribution (by ranges)
    marks_ranges = [
        ('90-100', 90, 100),
        ('80-89', 80, 89.99),
        ('70-79', 70, 79.99),
        ('60-69', 60, 69.99),
        ('50-59', 50, 59.99),
        ('40-49', 40, 49.99),
        ('0-39', 0, 39.99),
    ]
    
    marks_distribution = []
    for range_name, min_val, max_val in marks_ranges:
        count = results.filter(
            marks_obtained__gte=min_val,
            marks_obtained__lte=max_val
        ).count()
        percentage = (count / stats['count'] * 100) if stats['count'] > 0 else 0
        marks_distribution.append({
            'range': range_name,
            'count': count,
            'percentage': round(percentage, 1)
        })
    
    # Top performers
    top_performers = results.order_by('-marks_obtained')[:5]
    
    # Students needing improvement
    need_improvement = results.filter(marks_obtained__lt=50).order_by('marks_obtained')[:5]
    
    context = {
        'exam': exam,
        'teacher': teacher,
        'stats': stats,
        'grade_data': grade_data,
        'marks_distribution': marks_distribution,
        'top_performers': top_performers,
        'need_improvement': need_improvement,
        'total_students': stats['count'],
    }
    return render(request, 'teachers/exam_analysis.html', context)

@teacher_required
def subject_results(request, subject_id=None):
    """View results for teacher's subjects"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    
    # Get subjects taught by the teacher
    subjects = teacher.subjects.all()
    
    if subject_id:
        subject = get_object_or_404(Subject, id=subject_id)
        # Verify teacher teaches this subject
        if subject not in subjects:
            messages.error(request, "You don't teach this subject.")
            return redirect('subject_results')
        
        # Get exams for this subject
        exams = Exam.objects.filter(
            subject=subject,
            created_by=request.user
        ).order_by('-exam_date')
        
        # Get all results for this subject
        results = ExamResult.objects.filter(
            exam__subject=subject,
            exam__created_by=request.user
        ).select_related('exam', 'student').order_by('-exam__exam_date')
        
        # Calculate subject statistics with proper aggregation
        subject_stats = results.aggregate(
            avg_marks=Avg('marks_obtained'),
            total_exams=Count('exam', distinct=True),
            total_students=Count('student', distinct=True)
        )
    else:
        subject = None
        exams = []
        results = []
        subject_stats = {}
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'selected_subject': subject,
        'exams': exams,
        'results': results,
        'subject_stats': subject_stats,
    }
    return render(request, 'teachers/subject_results.html', context)

@teacher_required
def class_results(request, class_id=None):
    """View results for teacher's classes"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    if class_id:
        class_obj = get_object_or_404(Class, id=class_id)
        # Verify teacher is class teacher for this class
        if class_obj not in teacher_classes:
            messages.error(request, "You are not the class teacher for this class.")
            return redirect('class_results')
        
        # Get students in this class
        students = Student.objects.filter(
            current_class=class_obj,
            is_active=True
        ).order_by('roll_number')
        
        # Get all exams for this class
        exams = Exam.objects.filter(
            class_level=class_obj,
            created_by=request.user
        ).order_by('-exam_date')
        
        # Calculate class performance
        class_stats = {}
        if exams.exists():
            class_stats = ExamResult.objects.filter(
                exam__class_level=class_obj,
                exam__created_by=request.user
            ).aggregate(
                avg_marks=Avg('marks_obtained'),
                total_exams=Count('exam', distinct=True)
            )
    else:
        class_obj = None
        students = []
        exams = []
        class_stats = {}
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'selected_class': class_obj,
        'students': students,
        'exams': exams,
        'class_stats': class_stats,
    }
    return render(request, 'teachers/class_results.html', context)

@teacher_required
def generate_report_card(request, student_id, term=None):
    """Generate report card for a student"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    student = get_object_or_404(Student, id=student_id)
    
    # Verify student is in teacher's class
    if student.current_class not in Class.objects.filter(class_teacher=teacher):
        messages.error(request, "This student is not in your class.")
        return redirect('class_results')
    
    # Get current academic year
    academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    if not term:
        term = 'TERM1'  # Default to first term
    
    # Get all exam results for this student in the current academic year and term
    # Note: You might need to add term field to Exam model or implement term logic
    
    context = {
        'student': student,
        'teacher': teacher,
        'academic_year': academic_year,
        'term': term,
    }
    return render(request, 'teachers/report_card.html', context)

@teacher_required
def export_results_excel(request, exam_id):
    """Export exam results to Excel with comprehensive error handling"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('position')
    
    # Check if there are any results to export
    if not results.exists():
        messages.warning(request, 'No results available to export.')
        return redirect('exam_results', exam_id=exam.id)
    
    try:
        import pandas as pd
        from io import BytesIO
        
        # Create DataFrame with comprehensive data
        data = []
        for result in results:
            percentage = (float(result.marks_obtained) / float(exam.total_marks)) * 100
            data.append({
                'Position': result.position or '-',
                'Student ID': result.student.student_id,
                'Student Name': result.student.full_name,
                'Roll Number': result.student.roll_number,
                'Class': exam.class_level.name,
                'Marks Obtained': float(result.marks_obtained),
                'Total Marks': float(exam.total_marks),
                'Percentage': round(percentage, 2),
                'Grade': result.grade,
                'Remarks': result.remarks or '',
                'Status': 'Pass' if float(result.marks_obtained) >= float(exam.passing_marks or 0) else 'Fail'
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main results sheet
            df.to_excel(writer, sheet_name='Exam Results', index=False)
            
            # Summary statistics sheet
            summary_data = {
                'Exam Information': [
                    'Exam Name', 'Subject', 'Class', 'Exam Date', 
                    'Total Marks', 'Passing Marks', 'Total Students'
                ],
                'Details': [
                    exam.name,
                    exam.subject.name,
                    exam.class_level.name,
                    exam.exam_date.strftime('%Y-%m-%d'),
                    float(exam.total_marks),
                    float(exam.passing_marks or 0),
                    len(results)
                ]
            }
            
            stats_data = {
                'Statistics': [
                    'Average Marks', 'Highest Marks', 'Lowest Marks', 
                    'Pass Rate', 'Fail Rate'
                ],
                'Values': [
                    float(results.aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0),
                    float(results.aggregate(Max('marks_obtained'))['marks_obtained__max'] or 0),
                    float(results.aggregate(Min('marks_obtained'))['marks_obtained__min'] or 0),
                    f"{(results.filter(marks_obtained__gte=exam.passing_marks or 0).count() / len(results) * 100):.1f}%",
                    f"{(results.filter(marks_obtained__lt=exam.passing_marks or 0).count() / len(results) * 100):.1f}%"
                ]
            }
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Exam Summary', index=False)
            pd.DataFrame(stats_data).to_excel(writer, sheet_name='Statistics', index=False)
            
            # Grade distribution sheet
            grade_dist = results.values('grade').annotate(count=Count('id')).order_by('grade')
            grade_data = []
            for grade in grade_dist:
                grade_data.append({
                    'Grade': grade['grade'],
                    'Count': grade['count'],
                    'Percentage': f"{(grade['count'] / len(results) * 100):.1f}%"
                })
            pd.DataFrame(grade_data).to_excel(writer, sheet_name='Grade Distribution', index=False)
        
        output.seek(0)
        
        # Create HTTP response
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"{exam.name.replace(' ', '_')}_results_{exam.exam_date}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        messages.success(request, f'Results exported successfully to Excel!')
        return response
        
    except ImportError:
        # Fallback to CSV with user notification
        messages.info(request, 'Excel export not available. Downloading CSV format instead.')
        return export_results_csv(request, exam_id)
    except Exception as e:
        messages.error(request, f'Error exporting results: {str(e)}')
        return redirect('exam_results', exam_id=exam.id)

@teacher_required
def export_results_pdf(request, exam_id):
    """Export exam results to PDF"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('position')
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Add title
        title = Paragraph(f"Exam Results: {exam.name}", styles['Title'])
        elements.append(title)
        
        # Add exam details
        exam_details = [
            ['Subject:', str(exam.subject)],
            ['Class:', str(exam.class_level)],
            ['Exam Date:', exam.exam_date.strftime('%Y-%m-%d')],
            ['Total Marks:', str(exam.total_marks)]
        ]
        
        exam_table = Table(exam_details)
        exam_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))
        elements.append(exam_table)
        elements.append(Paragraph("<br/>", styles['Normal']))
        
        # Prepare results data
        results_data = [['Pos', 'Student ID', 'Name', 'Marks', 'Grade', 'Remarks']]
        
        for result in results:
            results_data.append([
                str(result.position),
                result.student.student_id,
                result.student.full_name,
                str(result.marks_obtained),
                result.grade,
                result.remarks or '-'
            ])
        
        # Create results table
        results_table = Table(results_data)
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(results_table)
        
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{exam.name}_results.pdf"'
        return response
        
    except ImportError:
        messages.error(request, "PDF export requires reportlab to be installed.")
        return redirect('exam_results', exam_id=exam_id)

@teacher_required
def bulk_upload_results(request, exam_id):
    """Bulk upload results via CSV"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    if request.method == 'POST':
        form = BulkResultForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            try:
                import csv
                import io
                
                csv_file = request.FILES['results_file']
                
                # Read the CSV file
                data_set = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                
                success_count = 0
                error_count = 0
                
                for row in csv.reader(io_string, delimiter=','):
                    if len(row) >= 2:
                        student_id = row[0].strip()
                        marks_obtained = row[1].strip()
                        remarks = row[2].strip() if len(row) > 2 else ''
                        
                        try:
                            # Find student
                            student = Student.objects.get(
                                student_id=student_id,
                                current_class=exam.class_level,
                                is_active=True
                            )
                            
                            # Create or update result
                            result, created = ExamResult.objects.update_or_create(
                                exam=exam,
                                student=student,
                                defaults={
                                    'marks_obtained': float(marks_obtained),
                                    'remarks': remarks
                                }
                            )
                            success_count += 1
                            
                        except Student.DoesNotExist:
                            error_count += 1
                        except ValueError:
                            error_count += 1
                
                # Recalculate positions
                calculate_exam_positions(exam)
                
                messages.success(
                    request, 
                    f'Successfully uploaded {success_count} results. {error_count} errors occurred.'
                )
                return redirect('exam_results', exam_id=exam.id)
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BulkResultForm(teacher=teacher, initial={'exam': exam})
    
    context = {
        'form': form,
        'exam': exam,
        'teacher': teacher,
    }
    return render(request, 'teachers/bulk_upload_results.html', context)

# AJAX views for teacher functionality
@teacher_required
@require_POST
def mark_attendance(request):
    """AJAX view to mark attendance"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        student_id = request.POST.get('student_id')
        date_str = request.POST.get('date')
        status = request.POST.get('status') == 'true'
        
        student = get_object_or_404(Student, id=student_id)
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Update or create attendance record
        attendance, created = Attendance.objects.update_or_create(
            student=student,
            date=attendance_date,
            defaults={
                'status': status,
                'marked_by': request.user,
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance marked for {student.full_name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@teacher_required
def get_class_students(request, class_id):
    """AJAX view to get students for a specific class"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        class_obj = get_object_or_404(Class, id=class_id)
        students = Student.objects.filter(
            current_class=class_obj,
            is_active=True
        ).order_by('roll_number')
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'name': student.full_name,
                'roll_number': student.roll_number,
                'student_id': student.student_id,
            })
        
        return JsonResponse({
            'success': True,
            'students': students_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@parent_required
def parent_dashboard(request):
    """Dashboard for parents with fee reminders"""
    try:
        # Check if user has parent profile
        if not hasattr(request.user, 'parent'):
            messages.error(request, "Parent profile not found. Please contact administration.")
            return redirect('login')
        
        parent = request.user.parent
        
        print(f"DEBUG: Parent dashboard loaded for {parent.user.username}")
        print(f"DEBUG: Parent data - Phone: {parent.phone}, Email: {parent.email}")
        print(f"DEBUG: Parent full_name: {parent.full_name}")
        
        # Get children using helper function
        children = get_parent_children(parent)
        print(f"DEBUG: Children found: {children.count()}")
        
        # Get dates for fee reminders
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        # Get fee reminders for parent's children
        overdue_fees = []
        upcoming_fees = []
        all_unpaid_fees = []
        
        # Fee statistics
        total_overdue = 0
        total_upcoming = 0
        total_unpaid = 0
        total_overdue_amount = 0
        total_upcoming_amount = 0
        
        if children.exists():
            try:
                # Get overdue fees (due date passed and status is unpaid)
                overdue_fees = Fee.objects.filter(
                    student__in=children,
                    status='unpaid',
                    due_date__lt=today
                ).select_related('student', 'student__current_class').order_by('due_date')
                
                # Get upcoming due fees (due in next 7 days)
                upcoming_fees = Fee.objects.filter(
                    student__in=children,
                    status='unpaid',
                    due_date__gte=today,
                    due_date__lte=next_week
                ).select_related('student', 'student__current_class').order_by('due_date')
                
                # Get all unpaid fees
                all_unpaid_fees = Fee.objects.filter(
                    student__in=children,
                    status='unpaid'
                ).select_related('student', 'student__current_class').order_by('due_date')
                
                # Calculate statistics
                total_overdue = overdue_fees.count()
                total_upcoming = upcoming_fees.count()
                total_unpaid = all_unpaid_fees.count()
                total_overdue_amount = overdue_fees.aggregate(Sum('amount'))['amount__sum'] or 0
                total_upcoming_amount = upcoming_fees.aggregate(Sum('amount'))['amount__sum'] or 0
                
                print(f"DEBUG: Overdue fees: {total_overdue}, Amount: ${total_overdue_amount}")
                print(f"DEBUG: Upcoming fees: {total_upcoming}, Amount: ${total_upcoming_amount}")
                print(f"DEBUG: All unpaid fees: {total_unpaid}")
                
            except Exception as e:
                print(f"DEBUG: Error getting fee reminders: {e}")
        
        # Initialize default data structures to avoid template errors
        attendance_summary = {}
        fee_status = {}
        
        # Get attendance summary for all children
        for child in children:
            try:
                child_attendance = Attendance.objects.filter(student=child).aggregate(
                    total_days=Count('id'),
                    present_days=Count('id', filter=Q(status=True)),
                    absent_days=Count('id', filter=Q(status=False))
                )
                attendance_summary[child.id] = child_attendance
                print(f"DEBUG: Attendance for {child.full_name}: {child_attendance}")
            except Exception as e:
                print(f"DEBUG: Error getting attendance for {child.full_name}: {e}")
                attendance_summary[child.id] = {'total_days': 0, 'present_days': 0, 'absent_days': 0}
        
        # Get upcoming exams
        upcoming_exams = []
        if children.exists():
            try:
                upcoming_exams = Exam.objects.filter(
                    class_level__in=children.values('current_class')
                ).order_by('exam_date')[:5]
                print(f"DEBUG: Upcoming exams: {upcoming_exams.count()}")
            except Exception as e:
                print(f"DEBUG: Error getting upcoming exams: {e}")
                upcoming_exams = []
        
        # Get fee status (different from fee reminders - this is summary per child)
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        for child in children:
            try:
                total_due = Fee.objects.filter(
                    student=child,
                    academic_year=current_academic_year
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                total_paid = FeePayment.objects.filter(
                    student=child,
                    fee__academic_year=current_academic_year
                ).aggregate(total=Sum('amount_paid'))['total'] or 0
                
                child_fees = {'total_due': total_due, 'total_paid': total_paid}
                fee_status[child.id] = child_fees
                print(f"DEBUG: Fees for {child.full_name}: {child_fees}")
            except Exception as e:
                print(f"DEBUG: Error getting fees for {child.full_name}: {e}")
                fee_status[child.id] = {'total_due': 0, 'total_paid': 0}
        
        # Get recent notices
        recent_notices = []
        try:
            recent_notices = Notice.objects.filter(
                Q(target_audience='ALL') | Q(target_audience='PARENTS'),
                is_active=True
            ).order_by('-publish_date')[:5]
            print(f"DEBUG: Recent notices: {recent_notices.count()}")
        except Exception as e:
            print(f"DEBUG: Error getting recent notices: {e}")
            recent_notices = []
        
        context = {
            'parent': parent,
            'children': children,
            'attendance_summary': attendance_summary,
            'upcoming_exams': upcoming_exams,
            'fee_status': fee_status,
            'recent_notices': recent_notices,
            
            # Fee reminders data
            'overdue_fees': overdue_fees,
            'upcoming_fees': upcoming_fees,
            'all_unpaid_fees': all_unpaid_fees,
            'today': today,
            'next_week': next_week,
            
            # Fee statistics
            'total_overdue': total_overdue,
            'total_upcoming': total_upcoming,
            'total_unpaid': total_unpaid,
            'total_overdue_amount': total_overdue_amount,
            'total_upcoming_amount': total_upcoming_amount,
        }
        
        print("DEBUG: Rendering parent dashboard template")
        return render(request, 'dashboard/parent_dashboard.html', context)
        
    except Exception as e:
        print(f"Parent dashboard error: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        messages.error(request, "Error loading parent dashboard.")
        # Return minimal context to avoid template errors
        return render(request, 'dashboard/parent_dashboard.html', {
            'parent': getattr(request.user, 'parent', None),
            'children': [],
            'attendance_summary': {},
            'upcoming_exams': [],
            'fee_status': {},
            'recent_notices': [],
            'overdue_fees': [],
            'upcoming_fees': [],
            'all_unpaid_fees': [],
            'today': timezone.now().date(),
            'next_week': timezone.now().date() + timedelta(days=7),
            'total_overdue': 0,
            'total_upcoming': 0,
            'total_unpaid': 0,
            'total_overdue_amount': 0,
            'total_upcoming_amount': 0,
        })


@parent_required
def check_fee_updates(request):
    """Check if there are fee updates for parent"""
    try:
        parent = request.user.parent
        children = get_parent_children(parent)
        
        # Get last check time from session
        last_check = request.session.get('last_fee_check', None)
        current_time = timezone.now()
        
        if last_check:
            last_check = parser.parse(last_check)
            # Check for new fees added since last check
            new_fees = Fee.objects.filter(
                student__in=children,
                created_at__gt=last_check
            ).exists()
            
            # Check for fee status changes
            updated_fees = Fee.objects.filter(
                student__in=children,
                updated_at__gt=last_check,
                created_at__lt=last_check
            ).exists()
            
            has_updates = new_fees or updated_fees
        else:
            has_updates = False
        
        # Update last check time
        request.session['last_fee_check'] = current_time.isoformat()
        
        return JsonResponse({
            'has_updates': has_updates,
            'timestamp': current_time.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'has_updates': False, 'error': str(e)})



@parent_required
def parent_fee_payments(request):
    """View all fee payments for parent - SIMPLIFIED VERSION"""
    try:
        print(f"DEBUG: Starting parent_fee_payments view")
        
        parent = request.user.parent
        
        # Get parent's children
        children = get_parent_children(parent)
        
        if not children.exists():
            messages.warning(request, "No children found in your account.")
            return render(request, 'parents/fee_payments.html', {
                'fees': [],
                'total_due': 0,
                'total_paid': 0,
                'children': children,
            })
        
        # Get all fees for children
        from core.models import Fee
        fees = Fee.objects.filter(
            student__in=children
        ).select_related('student', 'student__current_class').order_by('-due_date')
        
        # Calculate total due - manual calculation
        total_due = 0
        unpaid_fees = fees.filter(status='unpaid')
        for fee in unpaid_fees:
            total_due += float(fee.amount)
        
        # Calculate total paid - manual calculation
        from core.models import FeePayment
        fee_payments = FeePayment.objects.filter(student__in=children)
        total_paid = 0
        for payment in fee_payments:
            total_paid += float(payment.amount_paid)
        
        print(f"DEBUG: Total due: {total_due}, Total paid: {total_paid}")
        
        # Get fee payments for display
        fee_payments = fee_payments.select_related('fee', 'student').order_by('-payment_date')
        
        # Filter by status if specified
        status_filter = request.GET.get('status')
        if status_filter in ['paid', 'unpaid', 'partial']:
            fees = fees.filter(status=status_filter)
        
        # Filter by child if specified
        child_filter = request.GET.get('child')
        if child_filter:
            try:
                child_id = int(child_filter)
                if children.filter(id=child_id).exists():
                    fees = fees.filter(student_id=child_id)
                    fee_payments = fee_payments.filter(student_id=child_id)
            except (ValueError, TypeError):
                pass
        
        # Calculate paid amount for each fee
        for fee in fees:
            fee.total_paid = 0
            # Get payments for this specific fee
            payments_for_fee = FeePayment.objects.filter(fee=fee)
            for payment in payments_for_fee:
                fee.total_paid += float(payment.amount_paid)
            fee.balance = float(fee.amount) - fee.total_paid
        
        context = {
            'fees': fees,
            'fee_payments': fee_payments,
            'total_due': total_due,
            'total_paid': total_paid,
            'children': children,
            'status_filter': status_filter,
            'child_filter': child_filter,
        }
        
        return render(request, 'parents/fee_payments.html', context)
        
    except Exception as e:
        print(f"ERROR in parent_fee_payments: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error loading fee payments: {str(e)}")
        return redirect('parent_dashboard')


@parent_required
def make_payment(request, fee_id):
    """Make payment for a specific fee"""
    try:
        fee = get_object_or_404(Fee, id=fee_id)
        
        # Check if fee belongs to parent's child
        parent = request.user.parent
        children = get_parent_children(parent)
        
        if fee.student not in children:
            messages.error(request, "You are not authorized to pay this fee.")
            return redirect('parent_fee_payments')
        
        if request.method == 'POST':
            payment_method = request.POST.get('payment_method')
            amount = request.POST.get('amount')
            
            # Validate payment
            try:
                amount = float(amount)
                if amount <= 0:
                    messages.error(request, "Payment amount must be greater than 0.")
                elif amount > fee.remaining_amount():
                    messages.error(request, "Payment amount cannot exceed the remaining fee.")
                else:
                    # Create payment record
                    payment = FeePayment.objects.create(
                        fee=fee,
                        amount_paid=amount,
                        payment_method=payment_method,
                        payment_date=timezone.now().date(),
                        paid_by=parent.user.get_full_name(),
                        reference_number=f"PAY-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
                    )
                    
                    # Update fee status if fully paid
                    if fee.remaining_amount() <= 0:
                        fee.status = 'paid'
                        fee.save()
                    
                    messages.success(request, f"Payment of ${amount} processed successfully!")
                    return redirect('parent_fee_payments')
                    
            except ValueError:
                messages.error(request, "Invalid payment amount.")
        
        context = {
            'fee': fee,
            'payment_methods': ['CASH', 'MOBILE_MONEY', 'CREDIT_CARD', 'BANK_TRANSFER'],
        }
        
        return render(request, 'parents/make_payment.html', context)
        
    except Exception as e:
        print(f"Error in make_payment: {e}")
        messages.error(request, "Error processing payment.")
        return redirect('parent_fee_payments')


@parent_required
def payment_history(request):
    """View payment history for parent"""
    try:
        parent = request.user.parent
        children = get_parent_children(parent)
        
        # Get payments for children's fees
        payments = FeePayment.objects.filter(
            fee__student__in=children
        ).select_related('fee', 'fee__student').order_by('-payment_date')
        
        # Calculate total payments
        total_payments = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        # Filter by date range if specified
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            payments = payments.filter(payment_date__gte=start_date)
        if end_date:
            payments = payments.filter(payment_date__lte=end_date)
        
        context = {
            'payments': payments,
            'total_payments': total_payments,
            'start_date': start_date,
            'end_date': end_date,
            'children': children,
        }
        
        return render(request, 'parents/payment_history.html', context)
        
    except Exception as e:
        print(f"Error in payment_history: {e}")
        messages.error(request, "Error loading payment history.")
        return redirect('parent_dashboard')
# Add these views to views.py

@admin_required
def send_message_to_parent(request, parent_id):
    """Send message to parent"""
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        try:
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            
            if not subject or not content:
                messages.error(request, 'Subject and content are required!')
                return redirect('parent_details', parent_id=parent_id)
            
            # Create message
            Message.objects.create(
                sender=request.user,
                receiver=parent.user,
                subject=subject,
                content=content
            )
            
            messages.success(request, f'Message sent to {parent.full_name} successfully!')
            return redirect('parent_details', parent_id=parent_id)
            
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
    
    context = {
        'parent': parent,
    }
    return render(request, 'parents/send_message.html', context)

@admin_required
def link_children_to_parent(request, parent_id):
    """Link children to parent"""
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        try:
            student_ids = request.POST.getlist('students')
            
            # Get students
            students = Student.objects.filter(id__in=student_ids, is_active=True)
            
            # Link students to parent
            for student in students:
                parent.students.add(student)
            
            messages.success(request, f'Successfully linked {students.count()} children to {parent.full_name}!')
            return redirect('parent_details', parent_id=parent_id)
            
        except Exception as e:
            messages.error(request, f'Error linking children: {str(e)}')
    
    # Get students not already linked to this parent
    existing_children_ids = parent.students.values_list('id', flat=True)
    available_students = Student.objects.filter(
        is_active=True
    ).exclude(
        id__in=existing_children_ids
    ).order_by('first_name', 'last_name')
    
    context = {
        'parent': parent,
        'available_students': available_students,
    }
    return render(request, 'parents/link_children.html', context)

@parent_required
def parent_fee_history(request, parent_id):
    """View fee history for all children of a parent"""
    parent = get_object_or_404(Parent, id=parent_id)
    children = parent.students.filter(is_active=True)
    
    # Get current date for reminders
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    
    # Get fees for all children
    fees = Fee.objects.filter(
        student__in=children
    ).select_related('student', 'class_level', 'academic_year').order_by('-created_at')
    
    # Get overdue fees for this parent's children
    overdue_fees = fees.filter(
        status='unpaid',
        due_date__lt=today
    ).order_by('due_date')
    
    # Get upcoming fees for this parent's children
    upcoming_fees = fees.filter(
        status='unpaid',
        due_date__gte=today,
        due_date__lte=next_week
    ).order_by('due_date')
    
    # Get sent reminders for this parent's children using your existing Reminder model
    # Get all fees for this parent's children
    child_fees = Fee.objects.filter(student__in=children)
    sent_reminders = Reminder.objects.filter(
        fee__in=child_fees
    ).select_related('fee', 'fee__student').order_by('-sent_date')[:10]  # Last 10 reminders
    
    # Calculate totals
    total_due = fees.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = fees.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = fees.filter(status='unpaid').aggregate(total=Sum('amount'))['total'] or 0
    
    # Search and filter
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    child_filter = request.GET.get('child', '')
    
    if search_query:
        fees = fees.filter(
            Q(name__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )
    
    if status_filter:
        fees = fees.filter(status=status_filter)
    
    if child_filter:
        fees = fees.filter(student_id=child_filter)
    
    # Pagination
    paginator = Paginator(fees, 25)
    page_number = request.GET.get('page')
    fees_page = paginator.get_page(page_number)
    
    context = {
        'parent': parent,
        'children': children,
        'fees': fees_page,
        'overdue_fees': overdue_fees,
        'upcoming_fees': upcoming_fees,
        'sent_reminders': sent_reminders,  # Add this
        'total_due': total_due,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'search_query': search_query,
        'status_filter': status_filter,
        'child_filter': child_filter,
        'today': today,
    }
    return render(request, 'parents/fee_history.html', context)

@admin_required
def unlink_child(request, parent_id, student_id):
    """Unlink a child from parent"""
    parent = get_object_or_404(Parent, id=parent_id)
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            parent.students.remove(student)
            messages.success(request, f'{student.full_name} unlinked from {parent.full_name} successfully!')
        except Exception as e:
            messages.error(request, f'Error unlinking child: {str(e)}')
    
    return redirect('parent_details', parent_id=parent_id)

@admin_required
def all_students(request):
    students = Student.objects.all().order_by('current_class', 'roll_number')
    
    # Filtering
    class_filter = request.GET.get('class')
    if class_filter:
        students = students.filter(current_class_id=class_filter)
    
    section_filter = request.GET.get('section')
    if section_filter:
        students = students.filter(current_section_id=section_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )
    
    classes = Class.objects.all()
    sections = Section.objects.all()
    
    context = {
        'students': students,
        'classes': classes,
        'sections': sections,
    }
    return render(request, 'students/all_students.html', context)

@login_required
def student_details(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get student's attendance summary
    attendance_summary = Attendance.objects.filter(student=student).aggregate(
        total_days=Count('id'),
        present_days=Count('id', filter=Q(status=True)),
        absent_days=Count('id', filter=Q(status=False))
    )
    
    # Get exam results
    exam_results = ExamResult.objects.filter(student=student).select_related('exam', 'exam__subject')
    
    # Get fee payments
    fee_payments = FeePayment.objects.filter(student=student).select_related('fee')
    
    # Get parent information - FIXED: Use 'parents' instead of 'student_parents'
    parents = student.parents.all()
    
    context = {
        'student': student,
        'attendance_summary': attendance_summary,
        'exam_results': exam_results,
        'fee_payments': fee_payments,
        'parents': parents,
    }
    return render(request, 'students/student_details.html', context)

def generate_random_password(length=12):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for i in range(length))

# In your admit_form view, add this validation
def clean_parent_names(first_name, last_name):
    """Ensure names don't contain duplicates"""
    first_name = first_name.strip()
    last_name = last_name.strip()
    
    # Check if last_name contains first_name
    if first_name and last_name and first_name in last_name:
        # Remove the first name from last name
        last_name = last_name.replace(first_name, '').strip()
    
    # Check if first_name contains last_name  
    if last_name and first_name and last_name in first_name:
        # Remove the last name from first name
        first_name = first_name.replace(last_name, '').strip()
    
    return first_name, last_name


@admin_required
def admit_form(request):
    try:
        print("DEBUG: admit_form view called")
        
        if request.method == 'POST':
            try:
                # Extract and validate form data
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                date_of_birth = request.POST.get('date_of_birth')
                gender = request.POST.get('gender')
                class_level_id = request.POST.get('class_level')
                section_id = request.POST.get('section')
                
                # Parent information
                father_name = request.POST.get('father_name', '').strip()
                mother_name = request.POST.get('mother_name', '').strip()
                guardian_phone = request.POST.get('guardian_phone', '').strip()
                guardian_email = request.POST.get('guardian_email', '').strip()
                address = request.POST.get('address', '').strip()
                
                # Validate required fields
                if not all([first_name, last_name, date_of_birth, gender, class_level_id, 
                           father_name, mother_name, guardian_phone, guardian_email, address]):
                    messages.error(request, 'Please fill in all required fields.')
                    classes = Class.objects.all().order_by('name')
                    sections = Section.objects.all().order_by('name')
                    return render(request, 'students/admit_form.html', {
                        'classes': classes,
                        'sections': sections
                    })
                
                # Get class and section objects
                class_level = get_object_or_404(Class, id=class_level_id)
                section = get_object_or_404(Section, id=section_id) if section_id else None
                
                # Generate student ID and roll number
                year = timezone.now().year
                last_student = Student.objects.filter(admission_date__year=year).order_by('-id').first()
                if last_student:
                    last_id = int(last_student.student_id.split('-')[-1])
                    new_id = last_id + 1
                else:
                    new_id = 1
                student_id = f"STU-{year}-{new_id:04d}"
                
                # Generate roll number
                roll_number = f"RN{new_id:03d}"
                
                # Check if parent already exists by email
                existing_parent = Parent.objects.filter(email=guardian_email).first()
                
                if existing_parent:
                    parent_user = existing_parent.user
                    username = parent_user.username
                    password1 = "******** (Existing)"
                    # Update existing parent info if needed (optional)
                    print(f"DEBUG: Found existing parent: {existing_parent.full_name}")
                else:
                    # Generate parent username
                    username = guardian_email.split('@')[0]
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    # Generate parent password
                    provided_password = request.POST.get('parent_password', '').strip()
                    if provided_password:
                        password1 = provided_password
                    else:
                        parent_first_name = father_name.split()[0] if father_name and ' ' in father_name else father_name
                        parent_first_name = parent_first_name or (mother_name.split()[0] if mother_name and ' ' in mother_name else mother_name)
                        parent_first_name = parent_first_name or "Parent"
                        clean_name = parent_first_name.split()[0]
                        password1 = f"{clean_name.lower()}1234"
                    
                    # Create Parent User
                    parent_first_name = father_name or mother_name or "Parent"
                    parent_last_name = last_name
                    
                    parent_user = User.objects.create_user(
                        username=username,
                        email=guardian_email,
                        password=password1,
                        first_name=parent_first_name,
                        last_name=parent_last_name
                    )
                    
                    # Add to Parent group
                    from django.contrib.auth.models import Group
                    parent_group, created = Group.objects.get_or_create(name='Parent')
                    parent_user.groups.add(parent_group)
                    
                    # Create Parent profile
                    parent_profile = Parent.objects.create(
                        user=parent_user,
                        first_name=parent_first_name,
                        last_name=parent_last_name,
                        phone=guardian_phone,
                        email=guardian_email,
                        address=address,
                        father_name=father_name,
                        mother_name=mother_name,
                    )
                    print(f"DEBUG: New parent profile created: {parent_profile}")
                
                # Create AdmissionForm instance with CORRECT field names
                admission_data = {
                    # Student Information
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': date_of_birth,
                    'gender': gender,
                    'national_id': request.POST.get('national_id', '').strip(),
                    
                    # Academic Information
                    'class_level': class_level,
                    'section': section,
                    'previous_school': request.POST.get('previous_school', '').strip(),
                    'transfer_certificate_no': request.POST.get('transfer_certificate', '').strip(),
                    
                    # Parent Information
                    'father_name': father_name,
                    'father_occupation': request.POST.get('father_occupation', '').strip(),
                    'mother_name': mother_name,
                    'mother_occupation': request.POST.get('mother_occupation', '').strip(),
                    'guardian_phone': guardian_phone,
                    'guardian_email': guardian_email,
                    'address': address,
                    'city': request.POST.get('city', '').strip(),
                    'postal_code': request.POST.get('postal_code', '').strip(),
                    
                    # Emergency Contact
                    'emergency_contact_name': request.POST.get('emergency_contact_name', '').strip(),
                    'emergency_contact_phone': request.POST.get('emergency_contact_phone', '').strip(),
                    'emergency_relationship': request.POST.get('emergency_relationship', '').strip(),
                    
                    # Medical Information
                    'medical_conditions': request.POST.get('medical_conditions', '').strip(),
                    'medications': request.POST.get('medications', '').strip(),
                    'doctor_name': request.POST.get('doctor_name', '').strip(),
                    'doctor_phone': request.POST.get('doctor_phone', '').strip(),
                    
                    # Parent Login Information
                    'parent_username': username,
                    'parent_email': guardian_email,
                    'parent_password': password1,
                    
                    # Auto-generated fields
                    'admission_student_id': student_id,
                    'roll_number': roll_number,
                    'parent_user': parent_user,  # This should link to the User, not Parent
                }
                
                # Handle student photo separately
                if 'student_photo' in request.FILES:
                    admission_data['student_photo'] = request.FILES['student_photo']
                
                # Create the admission form
                admission = AdmissionForm.objects.create(**admission_data)
                print(f"DEBUG: Admission form created with ID: {admission.id}")
                
                # AUTO-APPROVE AND CREATE STUDENT
                if hasattr(admission, 'approve_admission'):
                    if admission.approve_admission(request.user):
                        # The student-parent link is now handled in the approve_admission method
                        # Just display success message
                        messages.success(request, f'Student {admission.first_name} {admission.last_name} admitted successfully! Student ID: {admission.admission_student_id}')
                        messages.info(request, f'Parent login created: Username: {username}, Password: {password1}')
                        return redirect('all_students')
                    else:
                        messages.error(request, f'Error creating student account for {admission.first_name} {admission.last_name}. Please try again.')
                        # Clean up
                        parent_user.delete()
                        admission.delete()
                        classes = Class.objects.all().order_by('name')
                        sections = Section.objects.all().order_by('name')
                        return render(request, 'students/admit_form.html', {
                            'classes': classes,
                            'sections': sections
                        })
                else:
                    messages.error(request, 'Approval method not available.')
                    parent_user.delete()
                    admission.delete()
                    classes = Class.objects.all().order_by('name')
                    sections = Section.objects.all().order_by('name')
                    return render(request, 'students/admit_form.html', {
                        'classes': classes,
                        'sections': sections
                    })
                
            except Exception as e:
                print(f"Error in POST processing: {e}")
                import traceback
                print(traceback.format_exc())
                messages.error(request, f'Error processing admission: {str(e)}')
                classes = Class.objects.all().order_by('name')
                sections = Section.objects.all().order_by('name')
                return render(request, 'students/admit_form.html', {
                    'classes': classes,
                    'sections': sections
                })
        
        # GET request - show empty form
        print("DEBUG: Handling GET request")
        classes = Class.objects.all().order_by('name')
        sections = Section.objects.all().order_by('name')
        
        print(f"DEBUG: Found {classes.count()} classes and {sections.count()} sections")
        
        context = {
            'classes': classes,
            'sections': sections,
        }
        
        if not classes.exists():
            messages.warning(request, 'No classes available. Please create classes first.')
        
        if not sections.exists():
            messages.warning(request, 'No sections available. Please create sections first.')
        
        print("DEBUG: Rendering template...")
        return render(request, 'students/admit_form.html', context)
        
    except Exception as e:
        print(f"DEBUG: Outer exception caught: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        messages.error(request, f'Unexpected error: {str(e)}')
        return redirect('admit_form')

@admin_required
def manage_admissions(request):
    """View to manage pending admissions"""
    all_admissions = AdmissionForm.objects.all().order_by('-submitted_date')
    
    status_filter = request.GET.get('status')
    if status_filter:
        admissions = all_admissions.filter(status=status_filter)
    else:
        admissions = all_admissions
        
    # Separate admissions for different tables
    pending_admissions = all_admissions.filter(status='PENDING')
    approved_admissions = all_admissions.filter(status='APPROVED')
    rejected_admissions = all_admissions.filter(status='REJECTED')
    
    # Get counts for statistics
    pending_count = pending_admissions.count()
    approved_count = approved_admissions.count()
    rejected_count = rejected_admissions.count()
    processed_count = approved_count + rejected_count
    
    context = {
        'admissions': admissions, # Keep for backward compatibility/filtering
        'pending_admissions': pending_admissions,
        'approved_admissions': approved_admissions,
        'rejected_admissions': rejected_admissions,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'processed_count': processed_count,
        'total_count': all_admissions.count(),
    }
    return render(request, 'students/manage_admissions.html', context)


@admin_required
def export_admissions_pdf(request):
    """Backend-generated PDF for admissions list (custom document)."""
    admissions = AdmissionForm.objects.all().order_by('-submitted_date')
    status_filter = request.GET.get('status')
    if status_filter:
        admissions = admissions.filter(status=status_filter)

    all_admissions = AdmissionForm.objects.all()
    context = {
        'admissions': admissions,
        'status_filter': status_filter,
        'generated_at': timezone.now(),
        'total_count': all_admissions.count(),
        'pending_count': all_admissions.filter(status='PENDING').count(),
        'approved_count': all_admissions.filter(status='APPROVED').count(),
        'rejected_count': all_admissions.filter(status='REJECTED').count(),
    }
    return render_template_to_pdf('print/admissions_list.html', context, filename='admissions_list.pdf')


@admin_required
def export_admission_detail_pdf(request, admission_id):
    """Backend-generated PDF for a single admission record (custom document)."""
    admission = get_object_or_404(AdmissionForm, id=admission_id)
    context = {
        'admission': admission,
        'generated_at': timezone.now(),
    }
    return render_template_to_pdf('print/admission_detail.html', context, filename=f'admission_{admission_id}.pdf')


@admin_required
def export_admissions_csv(request):
    """Backend-generated CSV export for admissions list."""
    admissions = AdmissionForm.objects.all().order_by('-submitted_date')
    status_filter = request.GET.get('status')
    if status_filter:
        admissions = admissions.filter(status=status_filter)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="admissions_list.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'id', 'status', 'submitted_date', 'admission_student_id',
        'first_name', 'last_name', 'gender', 'date_of_birth',
        'class_level', 'section', 'guardian_phone', 'guardian_email'
    ])
    for a in admissions:
        writer.writerow([
            a.id, a.status, a.submitted_date, a.admission_student_id,
            a.first_name, a.last_name, a.gender, a.date_of_birth,
            getattr(a.class_level, 'name', ''), getattr(a.section, 'name', ''),
            a.guardian_phone, a.guardian_email
        ])
    return response


@admin_required
def export_admissions_excel(request):
    """Backend-generated Excel export for admissions list."""
    admissions = AdmissionForm.objects.all().order_by('-submitted_date')
    status_filter = request.GET.get('status')
    if status_filter:
        admissions = admissions.filter(status=status_filter)

    wb = Workbook()
    ws = wb.active
    ws.title = "Admissions"

    headers = [
        'ID', 'Status', 'Submitted Date', 'Admission Student ID',
        'First Name', 'Last Name', 'Gender', 'Date of Birth',
        'Class', 'Section', 'Guardian Phone', 'Guardian Email'
    ]
    ws.append(headers)

    for a in admissions:
        ws.append([
            a.id, a.status,
            a.submitted_date.strftime('%Y-%m-%d %H:%M') if a.submitted_date else '',
            a.admission_student_id or '',
            a.first_name, a.last_name, a.get_gender_display(),
            a.date_of_birth.strftime('%Y-%m-%d') if a.date_of_birth else '',
            getattr(a.class_level, 'name', ''),
            getattr(a.section, 'name', ''),
            a.guardian_phone or '',
            a.guardian_email or ''
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="admissions_list.xlsx"'
    wb.save(response)
    return response

@admin_required
def approve_admission(request, admission_id):
    """Approve a specific admission"""
    admission = get_object_or_404(AdmissionForm, id=admission_id)
    
    if admission.status != 'PENDING':
        messages.warning(request, 'This admission has already been processed.')
        return redirect('manage_admissions')
    
    if hasattr(admission, 'approve_admission'):
        if admission.approve_admission(request.user):
            messages.success(request, f'Admission for {admission.first_name} {admission.last_name} approved successfully!')
        else:
            messages.error(request, 'Error approving admission. Please try again.')
    else:
        messages.error(request, 'Approval method not implemented.')
    
    return redirect('manage_admissions')

import logging
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.core.cache import cache
from django.db.models import Max, Prefetch, Q
from django.core.paginator import Paginator
from django.utils import timezone
from core.decorators import admin_required
from core.models import Student, Class, Section, AcademicYear, PromotionHistory, Fee

logger = logging.getLogger(__name__)

# Constants
CLASS_PROGRESSION = {
    'PP1': {'next': 'PP2', 'level': 1, 'phase': 'early_years'},
    'PP2': {'next': 'Grade 1', 'level': 2, 'phase': 'early_years'},
    'Grade 1': {'next': 'Grade 2', 'level': 3, 'phase': 'primary'},
    'Grade 2': {'next': 'Grade 3', 'level': 4, 'phase': 'primary'},
    'Grade 3': {'next': 'Grade 4', 'level': 5, 'phase': 'primary'},
    'Grade 4': {'next': 'Grade 5', 'level': 6, 'phase': 'primary'},
    'Grade 5': {'next': 'Grade 6', 'level': 7, 'phase': 'middle'},
    'Grade 6': {'next': 'Grade 7', 'level': 8, 'phase': 'middle'},
    'Grade 7': {'next': 'Grade 8', 'level': 9, 'phase': 'middle'},
    'Grade 8': {'next': 'Grade 9', 'level': 10, 'phase': 'high'},
    'Grade 9': {'next': None, 'level': 11, 'phase': 'high'},
}

ERROR_MESSAGES = {
    'max_grade': 'Student {name} ({student_id}) is already at maximum grade (Grade 9)',
    'class_not_found': 'Next class "{class_name}" does not exist in the system for student {name} ({student_id})',
    'duplicate_promotion': 'Student {name} ({student_id}) already promoted in {year}',
    'no_selection': 'Please select at least one student to promote',
    'missing_class': 'New class is required for manual promotion',
    'rate_limit': 'Daily promotion limit reached. Please try again tomorrow.',
}

def check_rate_limit(user):
    """Check if user has exceeded daily promotion limit"""
    key = f"promotion_limit_{user.id}_{timezone.now().date()}"
    count = cache.get(key, 0)
    if count >= 100:  # Max 100 promotions per day
        return False
    cache.set(key, count + 1, timeout=86400)  # 24 hours
    return True

def get_next_class(current_class_name):
    """Get the next class in the progression"""
    progression = CLASS_PROGRESSION.get(current_class_name)
    if progression and progression['next']:
        try:
            return Class.objects.get(name=progression['next'])
        except Class.DoesNotExist:
            return None
    return None

def validate_promotion_batch(students, academic_year):
    """Validate students for promotion and return warnings/errors"""
    warnings = []
    errors = []
    valid_students = []
    duplicate_promotions = []
    max_grade_students = []
    missing_class_students = []
    
    for student in students:
        # Check for duplicate promotion in same academic year
        if PromotionHistory.objects.filter(
            student=student,
            academic_year=academic_year
        ).exists():
            duplicate_promotions.append(student)
            warnings.append(ERROR_MESSAGES['duplicate_promotion'].format(
                name=student.get_full_name(),
                student_id=student.student_id,
                year=academic_year.name
            ))
            continue
        
        # Safety check for missing class
        if not student.current_class:
            missing_class_students.append(student)
            warnings.append(f"Student {student.get_full_name()} has no current class assigned and cannot be promoted.")
            continue
            
        # Check if student is at max grade
        progression = CLASS_PROGRESSION.get(student.current_class.name, {})
        if not progression or not progression.get('next'):
            max_grade_students.append(student)
            warnings.append(ERROR_MESSAGES['max_grade'].format(
                name=student.get_full_name(),
                student_id=student.student_id
            ))
            continue
        
        valid_students.append(student)
    
    return {
        'valid_students': valid_students,
        'warnings': warnings,
        'duplicate_promotions': duplicate_promotions,
        'max_grade_students': max_grade_students,
    }

@admin_required
@transaction.atomic
def student_promotion(request):
    """Handle student promotion operations"""
    
    if request.method == 'POST':
        return handle_promotion_post(request)
    
    # GET request handling
    return handle_promotion_get(request)

def handle_promotion_post(request):
    """Process promotion POST requests"""
    
    # Check rate limit
    if not check_rate_limit(request.user):
        messages.error(request, ERROR_MESSAGES['rate_limit'])
        return redirect('student_promotion')
    
    try:
        student_ids = request.POST.getlist('students')
        academic_year_id = request.POST.get('academic_year')
        promotion_type = request.POST.get('promotion_type', 'manual')
        
        # Filter out invalid IDs (e.g. 'undefined', empty strings)
        student_ids = [sid for sid in student_ids if sid and sid.isdigit()]
        
        # Validate student selection
        if not student_ids:
            messages.error(request, ERROR_MESSAGES['no_selection'])
            return redirect('student_promotion')
        
        # Validate manual promotion class selection
        if promotion_type == 'manual' and not request.POST.get('new_class'):
            messages.error(request, ERROR_MESSAGES['missing_class'])
            return redirect('student_promotion')
        
        # Get academic year
        if academic_year_id:
            try:
                academic_year = AcademicYear.objects.get(id=academic_year_id)
            except AcademicYear.DoesNotExist:
                messages.error(request, 'Selected academic year not found')
                return redirect('student_promotion')
        else:
            academic_year = AcademicYear.objects.filter(is_current=True).first()
            if not academic_year:
                academic_year = AcademicYear.objects.first()
        
        # Get students with related data
        students = Student.objects.filter(
            id__in=student_ids,
            is_active=True
        ).select_related(
            'current_class', 'current_section'
        )
        
        # Validate students before promotion
        validation_result = validate_promotion_batch(students, academic_year)
        
        # Process valid students
        promoted_student_ids = []
        promoted_count = 0
        
        for student in validation_result['valid_students']:
            old_class = student.current_class
            old_section = student.current_section
            
            if promotion_type == 'auto':
                # Auto promotion
                new_class = get_next_class(old_class.name)
                if not new_class:
                    validation_result['warnings'].append(ERROR_MESSAGES['class_not_found'].format(
                        class_name=CLASS_PROGRESSION.get(old_class.name, {}).get('next', 'Unknown'),
                        name=student.get_full_name(),
                        student_id=student.student_id
                    ))
                    continue
                # Try to find matching section in new class
                new_section = Section.objects.filter(class_name=new_class, name=old_section.name).first() if old_section else None
            else:
                # Manual promotion
                new_class = Class.objects.get(id=request.POST.get('new_class'))
                new_section_id = request.POST.get('new_section')
                if new_section_id:
                    new_section = Section.objects.get(id=new_section_id)
                else:
                    # Try to find matching section in new class if not specified
                    new_section = Section.objects.filter(class_name=new_class, name=old_section.name).first() if old_section else None
            
            # Update student
            student.current_class = new_class
            if new_section:
                student.current_section = new_section
            student.save()
            
            # Create promotion record
            PromotionHistory.objects.create(
                student=student,
                from_class=old_class,
                from_section=old_section,
                to_class=new_class,
                to_section=new_section,
                academic_year=academic_year,
                promoted_by=request.user,
                promotion_type=promotion_type,
            )
            promoted_student_ids.append(student.id)
            promoted_count += 1
        
        # Bulk update fees (optimized) - Only for successfully promoted students
        if academic_year and promoted_count > 0:
            Fee.objects.filter(
                student_id__in=promoted_student_ids,
                academic_year=AcademicYear.objects.filter(is_current=True).first()
            ).update(academic_year=academic_year)
        
        # Log the promotion
        logger.info(
            f"User {request.user.username} promoted {promoted_count} students "
            f"to {academic_year.name}"
        )
        
        # Prepare response messages
        if promoted_count > 0:
            messages.success(
                request,
                f'Successfully promoted {promoted_count} student(s) to {academic_year.name}.'
            )
        
        # Add warnings
        for warning in validation_result['warnings']:
            messages.warning(request, warning)
        
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if promoted_count > 0:
                return JsonResponse({
                    'success': True,
                    'promoted_count': promoted_count,
                    'skipped_count': len(students) - promoted_count,
                    'warnings': validation_result['warnings'][:5],
                    'redirect_url': reverse('promotion_history')
                })
            else:
                # No students promoted (e.g. all were duplicates or max grade)
                error_msg = validation_result['warnings'][0] if validation_result['warnings'] else "No students were promoted. They might already be promoted or at maximum grade."
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'promoted_count': 0,
                    'skipped_count': len(students),
                    'warnings': validation_result['warnings']
                })
        
        return redirect('promotion_history')
        
    except Exception as e:
        logger.error(f"Promotion error: {str(e)}", exc_info=True)
        error_msg = f'Error promoting students: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': error_msg},
                status=400
            )
        
        messages.error(request, error_msg)
        return redirect('student_promotion')

def handle_promotion_get(request):
    """Handle promotion GET requests - render the promotion page"""
    
    # Get active students with related data
    students = Student.objects.filter(
        is_active=True
    ).select_related(
        'current_class', 'current_section'
    ).order_by('current_class__name', 'first_name')
    
    # Get all classes and sections
    classes = Class.objects.all().order_by('name')
    sections = Section.objects.all().order_by('name')
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    # Get recent unique promotions (optimized query)
    recent_promotions = PromotionHistory.objects.all().select_related(
        'student', 'from_class', 'to_class', 'academic_year', 'promoted_by'
    ).order_by('-promotion_date')[:10]
    
    # Calculate stats
    total_students_count = students.count()
    promoted_this_year = PromotionHistory.objects.filter(
        promotion_date__year=timezone.now().year
    ).count()
    classes_count = classes.count()
    
    context = {
        'students': students,
        'classes': classes,
        'sections': sections,
        'academic_years': academic_years,
        'recent_promotions': recent_promotions,
        'total_students_count': total_students_count,
        'promoted_this_year': promoted_this_year,
        'classes_count': classes_count,
        'class_progression': CLASS_PROGRESSION,
    }
    
    return render(request, 'students/student_promotion.html', context)

@admin_required
def export_promotion_summary(request):
    """Export promotion history as CSV"""
    import csv
    from django.http import HttpResponse
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    promotions = PromotionHistory.objects.all()
    
    if start_date:
        promotions = promotions.filter(promotion_date__gte=start_date)
    if end_date:
        promotions = promotions.filter(promotion_date__lte=end_date)
    
    promotions = promotions.select_related(
        'student', 'from_class', 'to_class', 'academic_year', 'promoted_by'
    ).order_by('-promotion_date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="promotion_history.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Student ID', 'Student Name', 'From Class', 
        'To Class', 'Academic Year', 'Promoted By', 'Promotion Type'
    ])
    
    for p in promotions:
        writer.writerow([
            p.promotion_date.strftime('%Y-%m-%d %H:%M'),
            p.student.student_id,
            p.student.get_full_name(),
            p.from_class.name if p.from_class else 'N/A',
            p.to_class.name if p.to_class else 'N/A',
            p.academic_year.name if p.academic_year else 'N/A',
            p.promoted_by.get_full_name() or p.promoted_by.username,
            p.get_promotion_type_display()
        ])
    
    return response

    
from django.db.models.functions import TruncMonth
from django.db.models import Count, Max, Min
from collections import defaultdict
@admin_required
def promotion_history(request):
    """Enhanced promotion history view with better statistics"""
    # Base queryset
    promotions = PromotionHistory.objects.all().select_related(
        'student', 'from_class', 'to_class', 'academic_year', 'promoted_by'
    ).order_by('-promotion_date')
    
    # Apply filters
    filters = Q()
    
    class_filter = request.GET.get('class', '')
    if class_filter:
        filters &= Q(from_class_id=class_filter) | Q(to_class_id=class_filter)
    
    student_filter = request.GET.get('student', '')
    if student_filter:
        filters &= (
            Q(student__first_name__icontains=student_filter) |
            Q(student__last_name__icontains=student_filter) |
            Q(student__student_id__icontains=student_filter)
        )
    
    date_filter = request.GET.get('date', '')
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            filters &= Q(promotion_date__date=filter_date)
        except ValueError:
            pass
    
    academic_year_filter = request.GET.get('academic_year', '')
    if academic_year_filter:
        filters &= Q(academic_year_id=academic_year_filter)
    
    promotion_type_filter = request.GET.get('promotion_type', '')
    if promotion_type_filter:
        filters &= Q(promotion_type=promotion_type_filter)
    
    promotions = promotions.filter(filters)
    
    # Statistics
    total_promotions = promotions.count()
    
    # Unique students
    unique_students = promotions.values('student').distinct().count()
    
    # Monthly statistics
    current_year = datetime.now().year
    monthly_stats = promotions.filter(
        promotion_date__year=current_year
    ).annotate(
        month=TruncMonth('promotion_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Top promoters
    top_promoters = promotions.values(
        'promoted_by__username', 'promoted_by__first_name', 'promoted_by__last_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Most promoted classes
    from_class_stats = promotions.values('from_class__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    to_class_stats = promotions.values('to_class__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Date range
    date_range = promotions.aggregate(
        first_date=Min('promotion_date'),
        last_date=Max('promotion_date')
    )
    
    # Pagination
    paginator = Paginator(promotions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    classes = Class.objects.all().order_by('name')
    academic_years = AcademicYear.objects.all().order_by('-name')
    
    # Check for export
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_promotions_csv(promotions)
    elif export_format == 'pdf':
        return export_promotions_pdf(promotions)
    
    context = {
        'promotions': page_obj,
        'classes': classes,
        'academic_years': academic_years,
        'total_promotions_count': total_promotions,
        'unique_students_count': unique_students,
        'classes_count': classes.count(),
        'this_month_count': promotions.filter(
            promotion_date__month=datetime.now().month,
            promotion_date__year=datetime.now().year
        ).count(),
        'filtered_count': promotions.count(),
        'monthly_stats': monthly_stats,
        'top_promoters': top_promoters,
        'from_class_stats': from_class_stats,
        'to_class_stats': to_class_stats,
        'date_range': date_range,
        'promotion_type_choices': PromotionHistory.PROMOTION_TYPE_CHOICES,
    }
    
    return render(request, 'students/promotion_history.html', context)

def get_promotion_details(request):
    """AJAX view to get promotion details"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        promotion_id = request.GET.get('promotion_id')
        
        if not promotion_id:
            return JsonResponse({'error': 'Promotion ID required'}, status=400)
        
        try:
            promotion = PromotionHistory.objects.select_related(
                'student', 'from_class', 'to_class', 
                'academic_year', 'promoted_by'
            ).get(id=promotion_id)
            
            # Get student's complete promotion history
            student_history = list(
                PromotionHistory.objects.filter(
                    student=promotion.student
                ).order_by('promotion_date').values(
                    'id', 'promotion_date', 'from_class__name', 
                    'to_class__name', 'academic_year__name'
                )
            )
            
            data = {
                'success': True,
                'promotion': {
                    'id': promotion.id,
                    'date': promotion.promotion_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'student': {
                        'id': promotion.student.id,
                        'name': f"{promotion.student.first_name} {promotion.student.last_name}",
                        'student_id': promotion.student.student_id,
                        'current_class': promotion.student.current_class.name if promotion.student.current_class else 'N/A',
                        'current_section': promotion.student.current_section.name if promotion.student.current_section else 'N/A',
                        'email': promotion.student.email or 'N/A',
                        'phone': promotion.student.phone or 'N/A',
                    },
                    'from_class': promotion.from_class.name,
                    'from_section': promotion.from_section.name if promotion.from_section else 'Not specified',
                    'to_class': promotion.to_class.name,
                    'to_section': promotion.to_section.name if promotion.to_section else 'Not specified',
                    'academic_year': promotion.academic_year.name,
                    'promoted_by': {
                        'username': promotion.promoted_by.username,
                        'full_name': promotion.promoted_by.get_full_name() or promotion.promoted_by.username,
                        'email': promotion.promoted_by.email,
                    },
                    'promotion_type': promotion.get_promotion_type_display(),
                    'notes': promotion.notes or 'No additional notes',
                },
                'student_history': student_history,
                'student_promotion_count': len(student_history),
            }
            
            return JsonResponse(data)
            
        except PromotionHistory.DoesNotExist:
            return JsonResponse({'error': 'Promotion not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def revert_promotion(request):
    """AJAX view to revert (undo) a promotion record."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        promotion_id = request.POST.get('promotion_id')
        if not promotion_id:
            return JsonResponse({'error': 'Promotion ID required'}, status=400)
        try:
            promotion = PromotionHistory.objects.select_related(
                'student', 'from_class', 'from_section'
            ).get(id=promotion_id)

            student = promotion.student
            # Move the student back to the class they came FROM
            student.current_class = promotion.from_class
            if promotion.from_section:
                student.current_section = promotion.from_section
            student.save(update_fields=['current_class', 'current_section'])

            # Mark the original record as reverted
            promotion.is_reverted = True
            promotion.save(update_fields=['is_reverted'])

            # Create a NEW record for the reversion activity
            PromotionHistory.objects.create(
                student=student,
                from_class=promotion.to_class,    # Reverting FROM the class they were just promoted to
                from_section=promotion.to_section,
                to_class=promotion.from_class,    # BACK to the original class
                to_section=promotion.from_section,
                academic_year=promotion.academic_year,
                promoted_by=request.user,
                promotion_type='reversion',
                notes=f"Reverted promotion record ID: {promotion.id}"
            )

            return JsonResponse({
                'success': True,
                'message': f'{student.get_full_name()} has been moved back to {promotion.from_class.name}.'
            })

        except PromotionHistory.DoesNotExist:
            return JsonResponse({'error': 'Promotion record not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@admin_required
def update_student(request, student_id):
    """Update student information"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        try:
            # Update basic student information
            student.first_name = request.POST.get('first_name', student.first_name)
            student.last_name = request.POST.get('last_name', student.last_name)
            student.date_of_birth = request.POST.get('date_of_birth', student.date_of_birth)
            student.gender = request.POST.get('gender', student.gender)
            student.religion = request.POST.get('religion', student.religion)
            student.address = request.POST.get('address', student.address)
            student.phone = request.POST.get('phone', student.phone)
            student.email = request.POST.get('email', student.email)
            
            # Update academic information
            class_id = request.POST.get('current_class')
            section_id = request.POST.get('current_section')
            route_id = request.POST.get('transport_route')
            
            if class_id:
                student.current_class = get_object_or_404(Class, id=class_id)
            if section_id:
                student.current_section = get_object_or_404(Section, id=section_id)
            if route_id:
                student.transport_route = get_object_or_404(TransportRoute, id=route_id)
            elif 'transport_route' in request.POST: # Handle "None/Select" option
                student.transport_route = None
            
            student.roll_number = request.POST.get('roll_number', student.roll_number)
            
            # Update parent information
            student.father_name = request.POST.get('father_name', student.father_name)
            student.father_occupation = request.POST.get('father_occupation', student.father_occupation)
            student.father_phone = request.POST.get('father_phone', student.father_phone)
            student.mother_name = request.POST.get('mother_name', student.mother_name)
            student.mother_occupation = request.POST.get('mother_occupation', student.mother_occupation)
            student.mother_phone = request.POST.get('mother_phone', student.mother_phone)
            student.guardian_email = request.POST.get('guardian_email', student.guardian_email)
            student.guardian_phone = request.POST.get('guardian_phone', student.guardian_phone)
            
            # Update emergency contact
            student.emergency_contact_name = request.POST.get('emergency_contact_name', student.emergency_contact_name)
            student.emergency_contact_phone = request.POST.get('emergency_contact_phone', student.emergency_contact_phone)
            student.emergency_relationship = request.POST.get('emergency_relationship', student.emergency_relationship)
            
            # Update previous school information
            student.previous_school = request.POST.get('previous_school', student.previous_school)
            student.transfer_certificate_no = request.POST.get('transfer_certificate_no', student.transfer_certificate_no)
            
            # Update medical information
            student.medical_conditions = request.POST.get('medical_conditions', student.medical_conditions)
            student.medications = request.POST.get('medications', student.medications)
            student.doctor_name = request.POST.get('doctor_name', student.doctor_name)
            student.doctor_phone = request.POST.get('doctor_phone', student.doctor_phone)
            
            # Update national ID
            student.national_id = request.POST.get('national_id', student.national_id)
            
            # Handle photo upload
            if 'photo' in request.FILES:
                student.photo = request.FILES['photo']
            
            student.save()
            
            messages.success(request, f'Student {student.first_name} {student.last_name} updated successfully!')
            return redirect('student_details', student_id=student.student_id)
            
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
            print(f"Error updating student: {traceback.format_exc()}")
    
    # GET request - show edit form
    classes = Class.objects.all()
    sections = Section.objects.all()
    routes = TransportRoute.objects.all()
    
    context = {
        'student': student,
        'classes': classes,
        'sections': sections,
        'routes': routes,
    }
    return render(request, 'students/update_student.html', context)

@admin_required
def delete_student(request, student_id):
    """Delete a student (soft delete by setting is_active to False)"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        try:
            student_name = f"{student.first_name} {student.last_name}"
            student.is_active = False
            student.save()
            
            messages.success(request, f'Student {student_name} has been deleted successfully!')
            return redirect('all_students')
            
        except Exception as e:
            messages.error(request, f'Error deleting student: {str(e)}')
    
    # GET request - show confirmation page
    context = {
        'student': student,
    }
    return render(request, 'students/delete_student.html', context)

@admin_required
def restore_student(request, student_id):
    """Restore a soft-deleted student"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        try:
            student.is_active = True
            student.save()
            
            messages.success(request, f'Student {student.first_name} {student.last_name} has been restored successfully!')
            return redirect('student_details', student_id=student.student_id)
            
        except Exception as e:
            messages.error(request, f'Error restoring student: {str(e)}')
    
    return redirect('all_students')

@admin_required
def permanent_delete_student(request, student_id):
    """Permanently delete a student from database"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        try:
            student_name = f"{student.first_name} {student.last_name}"
            
            # Delete associated user if exists
            if student.user:
                student.user.delete()
            
            student.delete()
            
            messages.success(request, f'Student {student_name} has been permanently deleted!')
            return redirect('all_students')
            
        except Exception as e:
            messages.error(request, f'Error permanently deleting student: {str(e)}')
    
    # GET request - show confirmation page
    context = {
        'student': student,
    }
    return render(request, 'students/permanent_delete_student.html', context)

@admin_required
def all_teachers(request):
    teachers = Teacher.objects.select_related('class_teacher').prefetch_related('subjects', 'assigned_classes').all()
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        teachers = teachers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(teacher_id__icontains=search_query) |
            Q(qualification__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )

    # Filters
    subject_id = request.GET.get('subject')
    status = request.GET.get('status')
    gender = request.GET.get('gender')

    if subject_id:
        teachers = teachers.filter(subjects__id=subject_id)

    if status == 'active':
        teachers = teachers.filter(is_active=True)
    elif status == 'inactive':
        teachers = teachers.filter(is_active=False)

    if gender in ['M', 'F', 'O']:
        teachers = teachers.filter(gender=gender)

    # Sorting
    sort = request.GET.get('sort', 'name_asc')
    sort_mapping = {
        'name_asc': ['first_name', 'last_name'],
        'name_desc': ['-first_name', '-last_name'],
        'joining_newest': ['-joining_date'],
        'joining_oldest': ['joining_date'],
        'experience_high': ['-experience'],
        'experience_low': ['experience'],
    }

    order_by_fields = sort_mapping.get(sort, ['first_name', 'last_name'])
    teachers = teachers.order_by(*order_by_fields)
    
    # Calculate statistics
    total_teachers = teachers.count()
    active_teachers = teachers.filter(is_active=True).count()
    male_teachers = teachers.filter(gender='M', is_active=True).count()
    female_teachers = teachers.filter(gender='F', is_active=True).count()
    
    # Pagination
    paginator = Paginator(teachers, 25)  # Show 25 teachers per page
    page_number = request.GET.get('page')
    teachers_page = paginator.get_page(page_number)
    
    # Filter options
    subjects = Subject.objects.all().order_by('name')

    context = {
        'teachers': teachers_page,
        'search_query': search_query or '',
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'male_teachers': male_teachers,
        'female_teachers': female_teachers,
        'subjects': subjects,
        'selected_subject': subject_id or '',
        'selected_status': status or '',
        'selected_gender': gender or '',
        'selected_sort': sort,
    }
    return render(request, 'teachers/all_teachers.html', context)


@admin_required
def export_teachers_csv(request):
    """
    Export teachers as CSV, respecting current search/filters/sort.
    """
    teachers = Teacher.objects.all()

    # Reuse the same filtering logic as all_teachers
    search_query = request.GET.get('search')
    if search_query:
        teachers = teachers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(teacher_id__icontains=search_query) |
            Q(qualification__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )

    subject_id = request.GET.get('subject')
    status = request.GET.get('status')
    gender = request.GET.get('gender')

    if subject_id:
        teachers = teachers.filter(subjects__id=subject_id)

    if status == 'active':
        teachers = teachers.filter(is_active=True)
    elif status == 'inactive':
        teachers = teachers.filter(is_active=False)

    if gender in ['M', 'F', 'O']:
        teachers = teachers.filter(gender=gender)

    sort = request.GET.get('sort', 'name_asc')
    sort_mapping = {
        'name_asc': ['first_name', 'last_name'],
        'name_desc': ['-first_name', '-last_name'],
        'joining_newest': ['-joining_date'],
        'joining_oldest': ['joining_date'],
        'experience_high': ['-experience'],
        'experience_low': ['experience'],
    }
    order_by_fields = sort_mapping.get(sort, ['first_name', 'last_name'])
    teachers = teachers.order_by(*order_by_fields)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    filename = 'teachers.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Teacher ID',
        'First Name',
        'Last Name',
        'Gender',
        'Email',
        'Phone',
        'Qualification',
        'Specialization',
        'Experience (years)',
        'Teaching Level',
        'Joining Date',
        'Active',
        'Subjects',
    ])

    for teacher in teachers:
        subject_names = ', '.join(teacher.subjects.values_list('name', flat=True))
        writer.writerow([
            teacher.teacher_id,
            teacher.first_name,
            teacher.last_name,
            teacher.get_gender_display() if hasattr(teacher, 'get_gender_display') else teacher.gender,
            teacher.email,
            teacher.phone,
            teacher.qualification,
            teacher.specialization,
            teacher.experience,
            teacher.get_teaching_level_display() if hasattr(teacher, 'get_teaching_level_display') else teacher.teaching_level,
            teacher.joining_date,
            'Yes' if teacher.is_active else 'No',
            subject_names,
        ])

    return response

@admin_required
def teacher_details(request, teacher_id):
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    
    # Get classes assigned to this teacher
    classes_taught = teacher.assigned_classes.all()
    
    # Calculate total unique students across all assigned classes
    students_list = Student.objects.filter(current_class__in=classes_taught).select_related('current_class', 'current_section').distinct()
    total_students = students_list.count()
    
    context = {
        'teacher': teacher,
        'classes_taught': classes_taught,
        'total_students': total_students,
        'students_list': students_list,
    }
    return render(request, 'teachers/teacher_details.html', context)

@admin_required
def add_teacher(request):
    if request.method == 'POST':
        try:
            # Generate teacher ID if not provided
            teacher_id = request.POST.get('teacher_id')
            if not teacher_id:
                year = timezone.now().year
                last_teacher = Teacher.objects.filter(joining_date__year=year).order_by('-id').first()
                if last_teacher:
                    last_id = int(last_teacher.teacher_id.split('-')[-1])
                    new_id = last_id + 1
                else:
                    new_id = 1
                teacher_id = f"TCH-{year}-{new_id:04d}"
            
            # Create user
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password1'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name')
            )
            
            # Create teacher profile
            teacher = Teacher.objects.create(
                user=user,
                teacher_id=teacher_id,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                gender=request.POST.get('gender'),
                date_of_birth=request.POST.get('date_of_birth'),
                religion=request.POST.get('religion', ''),
                address=request.POST.get('address'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email'),
                qualification=request.POST.get('qualification'),
                specialization=request.POST.get('specialization'),
                experience=request.POST.get('experience', 0),
                teaching_level=request.POST.get('teaching_level', 'PRIMARY'),
                joining_date=request.POST.get('joining_date'),
                salary=request.POST.get('salary', 0),
                photo=request.FILES.get('photo')
            )
            
            # Add subjects
            subject_ids = request.POST.getlist('subjects')
            teacher.subjects.set(subject_ids)
            
            # Add to Teacher group
            from django.contrib.auth.models import Group
            teacher_group, created = Group.objects.get_or_create(name='Teacher')
            user.groups.add(teacher_group)
            
            # Handle Class Teacher Assignment
            class_teacher_id = request.POST.get('class_teacher')
            if class_teacher_id:
                target_class = get_object_or_404(Class, id=class_teacher_id)
                # Ensure class doesn't already have a teacher
                if target_class.class_teacher:
                    messages.warning(request, f'Class {target_class.name} already has a teacher. Skipping assignment.')
                else:
                    target_class.class_teacher = teacher
                    target_class.save()
                    teacher.class_teacher = target_class
                    teacher.save()

            # Handle Assigned Classes (M2M)
            assigned_class_ids = request.POST.getlist('assigned_classes')
            if assigned_class_ids:
                teacher.assigned_classes.set(assigned_class_ids)
            
            messages.success(request, f'Teacher {teacher.full_name} added successfully!')
            return redirect('all_teachers')
            
        except Exception as e:
            print(f"Add teacher error: {e}")
            messages.error(request, f'Error adding teacher: {str(e)}')
    
    # GET request - show form with context
    subjects = Subject.objects.all()
    # For add_teacher, all classes without a teacher are available
    available_classes = Class.objects.filter(class_teacher__isnull=True)
    all_classes = Class.objects.all()
    
    context = {
        'subjects': subjects,
        'today': timezone.now().date(),
        'classes': available_classes,
        'all_classes': all_classes,
    }
    return render(request, 'teachers/add_teacher.html', context)

@admin_required
def assign_teacher_classes(request, teacher_id):
    """Assign classes to a teacher"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    
    if request.method == 'POST':
        try:
            class_ids = request.POST.getlist('classes')
            
            # Clear current class assignments for this teacher
            Class.objects.filter(class_teacher=teacher).update(class_teacher=None)
            
            # Assign new classes
            if class_ids:
                # Security check: ensure none of these classes belong to someone else
                classes_to_assign = Class.objects.filter(id__in=class_ids)
                occupied_classes = classes_to_assign.filter(class_teacher__isnull=False).exclude(class_teacher=teacher)
                
                if occupied_classes.exists():
                    class_names = ", ".join([c.name for c in occupied_classes])
                    messages.error(request, f'Assignment failed: The following classes already have class teachers: {class_names}')
                    return redirect('assign_teacher_classes', teacher_id=teacher.teacher_id)

                classes_to_assign.update(class_teacher=teacher)
                
                messages.success(request, f'Successfully assigned {classes_to_assign.count()} classes to {teacher.full_name}!')
            else:
                messages.info(request, f'No classes assigned to {teacher.full_name}.')
            
            return redirect('teacher_details', teacher_id=teacher.teacher_id)
            
        except Exception as e:
            messages.error(request, f'Error assigning classes: {str(e)}')
    
    # GET request - show assignment form
    current_classes = Class.objects.filter(class_teacher=teacher)
    available_classes = Class.objects.filter(Q(class_teacher__isnull=True) | Q(class_teacher=teacher))
    
    # Calculate total students in current classes
    total_students = 0
    for class_obj in current_classes:
        total_students += class_obj.students.count()
    
    context = {
        'teacher': teacher,
        'current_classes': current_classes,
        'available_classes': available_classes,
        'total_students': total_students,
    }
    return render(request, 'teachers/assign_classes.html', context)

@admin_required
def remove_teacher_class(request, teacher_id, class_id):
    """Remove a specific class from a teacher"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    class_obj = get_object_or_404(Class, id=class_id, class_teacher=teacher)
    
    if request.method == 'POST':
        class_obj.class_teacher = None
        class_obj.save()
        
        messages.success(request, f'Class "{class_obj.name}" has been removed from {teacher.full_name}.')
        return redirect('teacher_details', teacher_id=teacher.teacher_id)
    
    context = {
        'teacher': teacher,
        'class_obj': class_obj,
    }
    return render(request, 'teachers/confirm_remove_class.html', context)

@admin_required
@require_GET
def get_subject_teachers(request):
    """AJAX: Get current teachers assigned to a subject"""
    subject_id = request.GET.get('subject_id')
    if not subject_id:
        return JsonResponse({'success': False, 'message': 'No subject provided'})

    try:
        subject = Subject.objects.get(id=subject_id)
        teachers_data = [
            {
                'id': teacher.id,
                'name': teacher.user.get_full_name() or teacher.user.username,
                'department': getattr(teacher, 'department', '')
            }
            for teacher in subject.teachers.all()
        ]
        return JsonResponse({'success': True, 'teachers': teachers_data})
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Subject not found'})

@admin_required
@require_POST
def assign_teachers_to_subject(request):
    """AJAX: Assign selected teachers to a subject"""
    subject_id = request.POST.get('subject_id')
    teacher_ids = request.POST.getlist('teachers[]')  # array from select multiple

    if not subject_id:
        return JsonResponse({'success': False, 'message': 'No subject provided'})

    try:
        subject = Subject.objects.get(id=subject_id)
        teachers = Teacher.objects.filter(id__in=teacher_ids)
        subject.teachers.set(teachers)  # replace existing assignments
        return JsonResponse({'success': True})
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Subject not found'})


@admin_required
def teacher_payment(request):
    if request.method == 'POST':
        try:
            # Get form data
            teacher_id = request.POST.get('teacher')
            amount = request.POST.get('amount')
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method')
            month = request.POST.get('month')
            year = request.POST.get('year')
            transaction_id = request.POST.get('transaction_id', '')
            remarks = request.POST.get('remarks', '')
            
            # Validate required fields
            if not all([teacher_id, amount, payment_date, payment_method, month, year]):
                messages.error(request, 'Please fill all required fields.')
                return redirect('teacher_payment')
            
            # Convert amount to decimal
            amount = Decimal(amount)
            
            # Get teacher
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Check if payment already exists for this month/year
            existing_payment = TeacherPayment.objects.filter(
                teacher=teacher,
                month=int(month),
                year=int(year)
            ).first()
            
            if existing_payment:
                messages.warning(request, f'Payment already exists for {teacher.full_name} for {month}/{year}.')
                return redirect('teacher_payment')
            
            # Create payment
            payment = TeacherPayment.objects.create(
                teacher=teacher,
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method,
                month=int(month),
                year=int(year),
                transaction_id=transaction_id,
                remarks=remarks,
                processed_by=request.user
            )
            
            # Send notification (if applicable)
            send_payment_notification(payment)
            
            messages.success(request, f'Payment of KSh {amount:,.2f} processed successfully for {teacher.full_name}.')
            return redirect('teacher_payment_history')
            
        except Teacher.DoesNotExist:
            messages.error(request, 'Teacher not found.')
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
            print(f"Payment error: {traceback.format_exc()}")
    
    # Get data for form
    teachers = Teacher.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    # Get current month and year
    today = timezone.now()
    current_month = today.month
    current_year = today.year
    
    # Get payment summary for current month
    current_month_payments = TeacherPayment.objects.filter(
        month=current_month,
        year=current_year
    ).aggregate(
        total_amount=Sum('amount'),
        payment_count=Count('id')
    )
    
    context = {
        'teachers': teachers,
        'current_month': current_month,
        'current_year': current_year,
        'month_choices': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'year_choices': [(y, y) for y in range(current_year - 5, current_year + 2)],
        'payment_methods': TeacherPayment.PAYMENT_METHODS,
        'total_monthly_payments': current_month_payments['total_amount'] or 0,
        'monthly_payment_count': current_month_payments['payment_count'] or 0,
    }
    return render(request, 'teachers/teacher_payment.html', context)


def teacher_payment_history(request):
    """View payment history with filters"""
    # Get filter parameters
    teacher_id = request.GET.get('teacher', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    payment_method = request.GET.get('payment_method', '')
    
    # Start with all payments
    payments = TeacherPayment.objects.all().select_related(
        'teacher', 'processed_by'
    ).order_by('-payment_date', '-created_at')
    
    # Apply filters
    if teacher_id:
        payments = payments.filter(teacher_id=teacher_id)
    
    if month:
        payments = payments.filter(month=int(month))
    
    if year:
        payments = payments.filter(year=int(year))
    
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    # Get summary statistics
    total_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    total_count = payments.count()
    
    # Calculate unique teachers count - FIXED
    unique_teachers_count = payments.values_list('teacher', flat=True).distinct().count()
    
    # Get distinct years for filter dropdown
    distinct_years = TeacherPayment.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    # Get month choices
    month_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    context = {
        'payments': payments,
        'teachers': Teacher.objects.filter(is_active=True),
        'total_amount': total_amount,
        'total_count': total_count,
        'unique_teachers_count': unique_teachers_count,  # Add this
        'selected_teacher': teacher_id,
        'selected_month': month,
        'selected_year': year,
        'selected_method': payment_method,
        'month_choices': month_choices,
        'year_choices': [(y, y) for y in distinct_years],
        'payment_methods': TeacherPayment.PAYMENT_METHODS,
    }
    return render(request, 'teachers/payment_history.html', context)


@admin_required
def delete_payment(request, payment_id):
    """Delete a payment record"""
    if request.method == 'POST':
        try:
            payment = TeacherPayment.objects.get(id=payment_id)
            teacher_name = payment.teacher.full_name
            payment.delete()
            
            messages.success(request, f'Payment record for {teacher_name} deleted successfully.')
            return redirect('teacher_payment_history')
            
        except TeacherPayment.DoesNotExist:
            messages.error(request, 'Payment record not found.')
        except Exception as e:
            messages.error(request, f'Error deleting payment: {str(e)}')
    
    return redirect('teacher_payment_history')


def send_payment_notification(payment):
    """Send payment notification to teacher (SMS/Email)"""
    try:
        teacher = payment.teacher
        
        # Prepare message
        message = f"Dear {teacher.first_name}, your salary payment of KSh {payment.amount:,.2f} "
        message += f"for {calendar.month_name[payment.month]} {payment.year} has been processed. "
        message += f"Payment method: {payment.get_payment_method_display()}. "
        message += "Thank you! - Petra Education Centre"
        
        # Send SMS if phone number exists
        if teacher.phone:
            # send_sms(teacher.phone, message)  # Implement your SMS gateway
            pass
        
        # Send email if email exists
        if teacher.email:
            subject = f"Salary Payment Notification - {calendar.month_name[payment.month]} {payment.year}"
            
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #4361ee;">Payment Processed Successfully</h2>
                <p>Dear {teacher.full_name},</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #28a745;">Payment Details:</h3>
                    <p><strong>Amount:</strong> KSh {payment.amount:,.2f}</p>
                    <p><strong>Period:</strong> {calendar.month_name[payment.month]} {payment.year}</p>
                    <p><strong>Payment Method:</strong> {payment.get_payment_method_display()}</p>
                    <p><strong>Transaction Date:</strong> {payment.payment_date}</p>
                    <p><strong>Transaction ID:</strong> {payment.transaction_id or 'N/A'}</p>
                </div>
                
                <p>Thank you for your dedication and hard work.</p>
                <p>Best regards,<br>
                Petra Education Centre<br>
                Accounts Department</p>
            </div>
            """
            
            send_mail(
                subject=subject,
                message=strip_tags(html_message),  # Plain text version
                from_email='accounts@petraeducation.ac.ke',
                recipient_list=[teacher.email],
                html_message=html_message,
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Error sending payment notification: {e}")


def payment_summary_report(request):
    """Generate payment summary report"""
    # Get filter parameters
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    
    # Default to current month/year
    today = timezone.now()
    if not month:
        month = today.month
    if not year:
        year = today.year
    
    # Get payments for selected period
    payments = TeacherPayment.objects.filter(
        month=int(month),
        year=int(year)
    ).select_related('teacher').order_by('teacher__first_name')
    
    # Calculate totals
    total_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Group by payment method
    payment_method_summary = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'payments': payments,
        'total_amount': total_amount,
        'payment_count': payments.count(),
        'selected_month': int(month),
        'selected_year': int(year),
        'month_name': calendar.month_name[int(month)],
        'payment_method_summary': payment_method_summary,
        'month_choices': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'year_choices': TeacherPayment.objects.values_list('year', flat=True).distinct().order_by('-year'),
    }
    
    return render(request, 'teachers/payment_summary.html', context)

@admin_required
def student_analytics(request):
    try:
        # Get total students count
        total_students = Student.objects.filter(is_active=True).count()
        
        # Get class statistics with proper formatting
        class_stats_raw = Student.objects.filter(is_active=True).values(
            'current_class__name'
        ).annotate(
            count=Count('id')
        ).order_by('current_class__name')
        
        # Format class stats for template
        class_stats = []
        for stat in class_stats_raw:
            class_name = stat['current_class__name'] or 'Not Assigned'
            class_stats.append({
                'class_name': class_name,
                'total_count': stat['count']
            })
        
        # Get gender statistics
        male_count = Student.objects.filter(is_active=True, gender='M').count()
        female_count = Student.objects.filter(is_active=True, gender='F').count()
        other_count = Student.objects.filter(is_active=True).exclude(gender__in=['M', 'F']).count()
        
        gender_stats = {
            'male': male_count,
            'female': female_count,
            'other': other_count,
            'total': total_students
        }
        
        # FIXED: Get admission trends (last 6 months) - More robust approach
        six_months_ago = timezone.now() - timedelta(days=180)
        
        # Generate last 6 months labels
        months = []
        current_date = timezone.now().date()
        for i in range(6):
            month_date = current_date - timedelta(days=30*i)
            month_label = month_date.strftime('%Y-%m')
            months.append(month_label)
        months.reverse()  # Show oldest to newest
        
        # Get admission data for each month
        admission_trends_data = []
        total_admission_count = 0
        
        for month_label in months:
            year, month = month_label.split('-')
            
            # Count admissions for this month
            try:
                if month_label == months[-1]:  # Current month
                    count = Student.objects.filter(
                        admission_date__year=int(year),
                        admission_date__month=int(month)
                    ).count()
                else:
                    count = Student.objects.filter(
                        admission_date__year=int(year),
                        admission_date__month=int(month)
                    ).count()
            except:
                count = 0
                
            admission_trends_data.append({
                'month': month_label,
                'count': count
            })
            total_admission_count += count
        
        # Alternative approach: Use AdmissionForm model if available
        if hasattr(__import__('core.models'), 'AdmissionForm'):
            try:
                # Try to get data from AdmissionForm for more accurate trends
                admission_form_trends = []
                for month_label in months:
                    year, month = month_label.split('-')
                    count = AdmissionForm.objects.filter(
                        submitted_date__year=int(year),
                        submitted_date__month=int(month),
                        status='APPROVED'
                    ).count()
                    admission_form_trends.append({
                        'month': month_label,
                        'count': count
                    })
                
                # Use AdmissionForm data if it has more meaningful data
                if sum(item['count'] for item in admission_form_trends) > 0:
                    admission_trends_data = admission_form_trends
                    total_admission_count = sum(item['count'] for item in admission_form_trends)
            except:
                pass
        
        # Get class-wise gender distribution
        class_gender_stats = []
        classes = Class.objects.all()
        
        for class_obj in classes:
            male_in_class = Student.objects.filter(
                current_class=class_obj, 
                is_active=True, 
                gender='M'
            ).count()
            
            female_in_class = Student.objects.filter(
                current_class=class_obj, 
                is_active=True, 
                gender='F'
            ).count()
            
            total_in_class = male_in_class + female_in_class
            
            if total_students > 0:
                percentage = (total_in_class / total_students) * 100
            else:
                percentage = 0
                
            class_gender_stats.append({
                'class_name': class_obj.name,
                'male_count': male_in_class,
                'female_count': female_in_class,
                'total_count': total_in_class,
                'percentage': round(percentage, 1)
            })
        
        # Get admission status counts
        admission_status = {
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'total': 0
        }
        
        if hasattr(__import__('core.models'), 'AdmissionForm'):
            try:
                admission_status['pending'] = AdmissionForm.objects.filter(status='PENDING').count()
                admission_status['approved'] = AdmissionForm.objects.filter(status='APPROVED').count()
                admission_status['rejected'] = AdmissionForm.objects.filter(status='REJECTED').count()
                admission_status['total'] = admission_status['pending'] + admission_status['approved'] + admission_status['rejected']
            except:
                pass
        
        context = {
            'total_students': total_students,
            'class_stats': class_stats,
            'gender_stats': gender_stats,
            'admission_trends': admission_trends_data,
            'class_gender_stats': class_gender_stats,
            'total_admission_count': total_admission_count,
            'admission_status': admission_status,
        }
        
        # Debug print
        print("DEBUG - Student Analytics Data:")
        print(f"Total Students: {total_students}")
        print(f"Class Stats: {class_stats}")
        print(f"Gender Stats: {gender_stats}")
        print(f"Admission Trends: {admission_trends_data}")
        print(f"Class Gender Stats: {class_gender_stats}")
        
        return render(request, 'dashboard/student_analytics.html', context)
        
    except Exception as e:
        print(f"Student analytics error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return basic context even if there are errors
        context = {
            'total_students': 0,
            'class_stats': [],
            'gender_stats': {'male': 0, 'female': 0, 'other': 0, 'total': 0},
            'admission_trends': [],
            'class_gender_stats': [],
            'total_admission_count': 0,
            'admission_status': {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0},
        }
        return render(request, 'dashboard/student_analytics.html', context)

@admin_required
def financial_overview(request):
    try:
        print("DEBUG: Starting financial overview...")
        
        # Calculate actual financial metrics from database
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        paid_expenses = Expense.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
        pending_expenses = Expense.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate revenue from fee payments
        total_revenue = FeePayment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
        net_profit = total_revenue - total_expenses
        
        # Get monthly expense data for charts
        current_year = timezone.now().year
        monthly_data = []
        monthly_labels = []
        
        for month in range(1, 13):
            month_expenses = Expense.objects.filter(
                date__year=current_year, 
                date__month=month
            ).aggregate(total=Sum('amount'))
            
            amount = month_expenses['total'] or 0
            monthly_data.append(float(amount))
            monthly_labels.append(datetime(current_year, month, 1).strftime('%b'))
        
        # Get expense by category data - FIXED: Create proper breakdown data
        expense_categories = []
        category_data = []
        category_labels = []
        category_colors = ['#4361ee', '#3a0ca3', '#7209b7', '#f72585', '#4cc9f0', '#560bad', '#b5179e']
        
        # Define expense types
        expense_types = getattr(Expense, 'EXPENSE_TYPES', [
            ('SALARY', 'Salaries'),
            ('UTILITIES', 'Utilities'),
            ('MAINTENANCE', 'Maintenance'),
            ('SUPPLIES', 'Supplies'),
            ('OTHER', 'Other')
        ])
        
        # Create breakdown data for the table
        expense_breakdown = []
        
        for i, (category_key, category_name) in enumerate(expense_types):
            category_total = Expense.objects.filter(
                expense_type=category_key
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            if category_total > 0:
                # For charts
                expense_categories.append({
                    'name': category_name,
                    'color': category_colors[i % len(category_colors)]
                })
                category_data.append(float(category_total))
                category_labels.append(category_name)
                
                # For breakdown table
                percentage = (category_total / total_expenses * 100) if total_expenses > 0 else 0
                expense_breakdown.append({
                    'name': category_name,
                    'amount': category_total,
                    'percentage': round(percentage, 1),
                    'color': category_colors[i % len(category_colors)]
                })
        
        # If no categories have data, create default data
        if not category_data:
            category_data = [1]
            category_labels = ['No Expenses']
            category_colors = ['#858796']
            expense_categories = [{'name': 'No Expenses', 'color': '#858796'}]
            expense_breakdown = [{
                'name': 'No Expenses',
                'amount': 0,
                'percentage': 0,
                'color': '#858796'
            }]
        
        # Get recent transactions
        recent_transactions = Expense.objects.all().order_by('-date')[:10]
        
        context = {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'paid_expenses': paid_expenses,
            'pending_expenses': pending_expenses,
            'net_profit': net_profit,
            'pending_payments': Expense.objects.filter(status='pending').count(),
            
            # Chart data
            'monthly_labels': json.dumps(monthly_labels),
            'monthly_expenses': json.dumps(monthly_data),
            
            # Pie chart data
            'expense_categories': expense_categories,
            'category_labels': json.dumps(category_labels),
            'category_data': json.dumps(category_data),
            'category_colors': json.dumps(category_colors[:len(category_labels)]),
            
            # Breakdown data for table
            'expense_breakdown': expense_breakdown,
            
            # Recent transactions
            'recent_transactions': recent_transactions
        }
        
        print(f"DEBUG: Expense breakdown: {expense_breakdown}")
        return render(request, 'finances/financial_overview.html', context)
        
    except Exception as e:
        print(f"ERROR in financial_overview: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return safe defaults
        context = {
            'total_revenue': 0,
            'total_expenses': 0,
            'paid_expenses': 0,
            'pending_expenses': 0,
            'net_profit': 0,
            'pending_payments': 0,
            'monthly_labels': json.dumps(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']),
            'monthly_expenses': json.dumps([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            'expense_categories': [{'name': 'No Data', 'color': '#858796'}],
            'category_labels': json.dumps(['No Data']),
            'category_data': json.dumps([1]),
            'category_colors': json.dumps(['#858796']),
            'expense_breakdown': [],
            'recent_transactions': []
        }
        return render(request, 'finances/financial_overview.html', context)

@admin_required
def expense_management(request):
    expenses = Expense.objects.all().order_by('-date')
    
    # Search and filter functionality
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    date_filter = request.GET.get('date', '')
    
    if search_query:
        expenses = expenses.filter(
            Q(name__icontains=search_query) |
            Q(expense_id__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if status_filter:
        expenses = expenses.filter(status=status_filter)
    
    if type_filter:
        expenses = expenses.filter(expense_type=type_filter)
    
    if date_filter:
        expenses = expenses.filter(date=date_filter)
    
    # Pagination
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'expenses': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'date_filter': date_filter,
    }
    return render(request, 'finances/expense_management.html', context)

@admin_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, f'Expense "{expense.name}" has been added successfully!')
            return redirect('expense_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExpenseForm()
    
    context = {
        'form': form,
        'title': 'Add New Expense'
    }
    return render(request, 'finances/expense_form.html', context)

@admin_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f'Expense "{expense.name}" has been updated successfully!')
            return redirect('expense_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExpenseForm(instance=expense)
    
    context = {
        'form': form,
        'title': 'Edit Expense',
        'expense': expense
    }
    return render(request, 'finances/expense_form.html', context)

@admin_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        expense_name = expense.name
        expense.delete()
        messages.success(request, f'Expense "{expense_name}" has been deleted successfully!')
        return redirect('expense_management')
    
    context = {
        'expense': expense
    }
    return render(request, 'finances/confirm_delete.html', context)

@admin_required
def expense_detail(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    
    context = {
        'expense': expense
    }
    return render(request, 'finances/expense_detail.html', context)

# AJAX view for expense statistics
@admin_required
def expense_statistics(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        paid_expenses = Expense.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
        pending_expenses = Expense.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
        
        data = {
            'total_expenses': float(total_expenses),
            'paid_expenses': float(paid_expenses),
            'pending_expenses': float(pending_expenses),
            'expense_count': Expense.objects.count(),
        }
        return JsonResponse(data)

# CORRECTED Fee Views - Fixed class_name to class_level
@admin_required
def add_fee(request):
    # Get all active students with their class and section information
    students = Student.objects.filter(is_active=True).select_related(
        'current_class', 'current_section'
    ).order_by('current_class__name', 'roll_number')
    
    # Get academic years and classes for the form
    academic_years = AcademicYear.objects.all()
    classes = Class.objects.all()
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Debug: Print student data to console
    print("=== STUDENT DATA DEBUG ===")
    for student in students:
        print(f"Student: {student.full_name}")
        print(f"  - ID: {student.id}")
        print(f"  - Student ID: {student.student_id}")
        print(f"  - Class: {student.current_class}")
        print(f"  - Class ID: {student.current_class.id if student.current_class else 'None'}")
        print(f"  - Section: {student.current_section}")
        print("---")
    
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.created_by = request.user
            fee.save()
            messages.success(request, f'Fee has been created successfully!')
            return redirect('all_fees')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-populate with current academic year
        initial_data = {}
        if current_academic_year:
            initial_data['academic_year'] = current_academic_year
        form = FeeForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Add New Fee',
        'students': students,
        'academic_years': academic_years,
        'classes': classes,
        'current_academic_year': current_academic_year,
    }
    return render(request, 'finances/fees/add_fee.html', context)

@admin_required
def all_fees(request):
    fees_list = Fee.objects.all().select_related('student', 'class_level', 'academic_year', 'created_by').order_by('-created_at')
    
    # Search functionality
    search_name = request.GET.get('search_name', '')
    search_class = request.GET.get('search_class', '')
    search_type = request.GET.get('search_type', '')
    
    if search_name:
        fees_list = fees_list.filter(
            Q(name__icontains=search_name) |
            Q(description__icontains=search_name) |
            Q(student__first_name__icontains=search_name) |
            Q(student__last_name__icontains=search_name)
        )
    
    if search_class:
        fees_list = fees_list.filter(class_level_id=search_class)
    
    if search_type:
        fees_list = fees_list.filter(fee_type=search_type)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        fees_list = fees_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(fees_list, 25)
    page_number = request.GET.get('page')
    fees = paginator.get_page(page_number)
    
    classes = Class.objects.all()
    
    context = {
        'fees': fees,
        'search_name': search_name,
        'search_class': search_class,
        'search_type': search_type,
        'status_filter': status_filter,
        'classes': classes,
    }
    return render(request, 'finances/fees/all_fees.html', context)

@admin_required
@require_POST
@csrf_exempt  # Add this to temporarily bypass CSRF for testing
def bulk_fee_actions(request):
    """Handle bulk actions for fees"""
    try:
        action = request.POST.get('action')
        fee_ids = request.POST.getlist('fee_ids[]')  # Note the [] for array data
        
        print(f"DEBUG: Received bulk action: {action}")
        print(f"DEBUG: Fee IDs: {fee_ids}")
        
        if not fee_ids:
            return JsonResponse({'success': False, 'message': 'No fees selected.'})
        
        # Convert string IDs to integers
        fee_ids = [int(fee_id) for fee_id in fee_ids]
        fees = Fee.objects.filter(id__in=fee_ids)
        
        print(f"DEBUG: Found {fees.count()} fees to process")
        
        if action == 'mark_paid':
            updated_count = fees.update(status='paid', paid_date=timezone.now().date())
            return JsonResponse({
                'success': True, 
                'message': f'Successfully marked {updated_count} fee(s) as paid.'
            })
            
        elif action == 'mark_unpaid':
            updated_count = fees.update(status='unpaid', paid_date=None)
            return JsonResponse({
                'success': True, 
                'message': f'Successfully marked {updated_count} fee(s) as unpaid.'
            })
            
        elif action == 'delete':
            deleted_count = fees.count()
            fees.delete()
            return JsonResponse({
                'success': True, 
                'message': f'Successfully deleted {deleted_count} fee record(s).'
            })
            
        elif action == 'send_reminder':
            # Implement reminder logic here
            return JsonResponse({
                'success': True, 
                'message': f'Reminders sent for {fees.count()} fee(s).'
            })
            
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action.'})
            
    except Exception as e:
        print(f"ERROR in bulk_fee_actions: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

@admin_required
def fee_reminders(request):
    """View all fee reminders and overdue fees"""
    # Get current date
    today = timezone.now().date()
    
    # Get overdue fees (due date passed and status is unpaid)
    overdue_fees = Fee.objects.filter(
        status='unpaid',
        due_date__lt=today
    ).select_related('student', 'student__current_class', 'student__current_section')
    
    # Get upcoming due fees (due in next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_fees = Fee.objects.filter(
        status='unpaid',
        due_date__gte=today,
        due_date__lte=next_week
    ).select_related('student', 'student__current_class', 'student__current_section')
    
    # Get all unpaid fees
    all_unpaid_fees = Fee.objects.filter(
        status='unpaid'
    ).select_related('student', 'student__current_class', 'student__current_section')
    
    # Get recent sent reminders (you'll need to create a FeeReminder model)
    recent_reminders = []  # Placeholder - you'll implement this later
    
    # Calculate statistics
    total_overdue = overdue_fees.count()
    total_upcoming = upcoming_fees.count()
    total_unpaid = all_unpaid_fees.count()
    total_overdue_amount = overdue_fees.aggregate(Sum('amount'))['amount__sum'] or 0
    total_upcoming_amount = upcoming_fees.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Filter by class if specified
    class_filter = request.GET.get('class')
    if class_filter:
        overdue_fees = overdue_fees.filter(student__current_class_id=class_filter)
        upcoming_fees = upcoming_fees.filter(student__current_class_id=class_filter)
        all_unpaid_fees = all_unpaid_fees.filter(student__current_class_id=class_filter)
    
    context = {
        'overdue_fees': overdue_fees,
        'upcoming_fees': upcoming_fees,
        'all_unpaid_fees': all_unpaid_fees,
        'recent_reminders': recent_reminders,
        'classes': Class.objects.all(),
        'today': today,
        'next_week': next_week,
        
        # Statistics
        'total_overdue': total_overdue,
        'total_upcoming': total_upcoming,
        'total_unpaid': total_unpaid,
        'total_overdue_amount': total_overdue_amount,
        'total_upcoming_amount': total_upcoming_amount,
        
        # Filter
        'class_filter': class_filter,
    }
    return render(request, 'finances/fee_reminders.html', context)

@admin_required
@require_POST
def send_fee_reminder(request, fee_id):
    """Send reminder for a specific fee"""
    try:
        fee = get_object_or_404(Fee, id=fee_id)
        
        # Here you would implement your email/SMS sending logic
        # For now, we'll just create a log entry
        
        # Create reminder record (you might want to create a FeeReminder model)
        print(f"DEBUG: Sending reminder for fee ID {fee_id}")
        print(f"DEBUG: Student: {fee.student.full_name}")
        print(f"DEBUG: Amount: {fee.amount}")
        print(f"DEBUG: Due Date: {fee.due_date}")
        
        messages.success(request, f'Reminder sent to {fee.student.full_name} for fee: {fee.name}')
        return redirect('fee_reminders')
        
    except Exception as e:
        messages.error(request, f'Error sending reminder: {str(e)}')
        return redirect('fee_reminders')

@admin_required
def send_bulk_reminders(request):
    """Send reminders for multiple fees at once"""
    if request.method == 'POST':
        fee_ids_param = request.POST.get('fee_ids', '')
        
        if not fee_ids_param:
            messages.error(request, 'No fees selected for reminders.')
            return redirect('fee_reminders')
        
        try:
            if fee_ids_param == 'all':
                # Send reminders for all overdue fees (unpaid and overdue)
                today = timezone.now().date()
                fees = Fee.objects.filter(
                    status='unpaid',  # Use status instead of is_paid
                    due_date__lt=today
                ).select_related('student')
                fee_count = fees.count()
            else:
                # Send reminders for selected fees - handle comma-separated IDs
                fee_ids = [int(fid.strip()) for fid in fee_ids_param.split(',') if fid.strip()]
                fees = Fee.objects.filter(
                    id__in=fee_ids,
                    status='unpaid'  # Use status instead of is_paid
                ).select_related('student')
                fee_count = fees.count()
            
            # Check if we should mark as paid instead (from the bulk action)
            mark_paid = request.POST.get('mark_paid') == 'true'
            
            if mark_paid:
                # Mark selected fees as paid
                updated_count = fees.update(
                    status='paid',  # Use status instead of is_paid
                    paid_date=timezone.now().date()  # Use paid_date instead of payment_date
                )
                messages.success(request, f'Successfully marked {updated_count} fees as paid.')
                return redirect('fee_reminders')
            
            # Send reminders logic here
            successful_reminders = 0
            failed_reminders = 0
            
            for fee in fees:
                try:
                    # Create reminder record
                    Reminder.objects.create(
                        fee=fee,
                        student_name=f"{fee.student.first_name} {fee.student.last_name}",
                        fee_type=fee.get_fee_type_display(),
                        sent_via='email',
                        status='sent',
                        notes=f"Reminder sent for {fee.get_fee_type_display()} fee of KES {fee.amount}"
                    )
                    
                    # TODO: Add your actual email/SMS sending logic here
                    # Example:
                    # send_fee_reminder_email(fee)
                    # send_fee_reminder_sms(fee)
                    
                    successful_reminders += 1
                    
                except Exception as e:
                    print(f"Failed to send reminder for fee {fee.id}: {str(e)}")
                    failed_reminders += 1
            
            if successful_reminders > 0:
                messages.success(
                    request, 
                    f'Successfully sent {successful_reminders} fee reminder(s)!'
                )
            if failed_reminders > 0:
                messages.warning(
                    request,
                    f'Failed to send {failed_reminders} reminder(s). Please check the logs.'
                )
            
            if successful_reminders == 0 and failed_reminders > 0:
                messages.error(request, 'Failed to send any reminders. Please try again.')
                
        except Exception as e:
            messages.error(request, f'Error processing bulk reminders: {str(e)}')
        
        return redirect('fee_reminders')
    
    return redirect('fee_reminders')

@admin_required
def mark_bulk_paid(request):
    """Mark multiple fees as paid at once"""
    if request.method == 'POST':
        fee_ids_param = request.POST.get('fee_ids', '')
        
        if not fee_ids_param:
            messages.error(request, 'No fees selected to mark as paid.')
            return redirect('fee_reminders')
        
        try:
            if fee_ids_param == 'all':
                # Mark all overdue fees as paid
                today = timezone.now().date()
                fees = Fee.objects.filter(
                    status='unpaid',  # Use status instead of is_paid
                    due_date__lt=today
                )
                fee_count = fees.count()
            else:
                # Mark selected fees as paid - handle comma-separated IDs
                fee_ids = [int(fid.strip()) for fid in fee_ids_param.split(',') if fid.strip()]
                fees = Fee.objects.filter(
                    id__in=fee_ids, 
                    status='unpaid'  # Use status instead of is_paid
                )
                fee_count = fees.count()
            
            # Update the fees
            updated_count = fees.update(
                status='paid',  # Use status instead of is_paid
                paid_date=timezone.now().date()  # Use paid_date instead of payment_date
            )
            
            messages.success(
                request, 
                f'Successfully marked {updated_count} fee(s) as paid.'
            )
            
        except Exception as e:
            messages.error(request, f'Error marking fees as paid: {str(e)}')
        
        return redirect('fee_reminders')
    
    return redirect('fee_reminders')

@admin_required
def mark_paid(request, fee_id):
    """Mark a single fee as paid"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('login')
    
    fee = get_object_or_404(Fee, id=fee_id)
    try:
        fee = get_object_or_404(Fee, id=fee_id)
        fee.is_paid = True
        fee.payment_date = timezone.now().date()
        fee.save()
        
        messages.success(
            request, 
            f'Fee marked as paid for {fee.student.first_name} {fee.student.last_name}.'
        )
        
    except Exception as e:
        messages.error(request, f'Error marking fee as paid: {str(e)}')
    
    return redirect('fee_reminders')

@admin_required
def send_fee_reminder_email(fee, request):
    subject = f'Fee Reminder: {fee.name} - {fee.student.current_class.name}'
    context = {
        'fee': fee,
        'student': fee.student,
        'today': timezone.now().date(),
    }
    message = render_to_string('emails/fee_reminder.html', context)
    
    if fee.student.guardian_email:
        send_mail(
            subject,
            message,
            'noreply@petra.edu',
            [fee.student.guardian_email],
            html_message=message,
            fail_silently=False,
        )

@parent_required
def fee_detail(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    context = {
        'fee': fee
    }
    return render(request, 'finances/fees/fee_detail.html', context)

@admin_required
def edit_fee(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    
    if request.method == 'POST':
        form = FeeForm(request.POST, instance=fee)
        if form.is_valid():
            try:
                # Ensure class_level is set from the student's current class
                updated_fee = form.save(commit=False)
                if not updated_fee.class_level and updated_fee.student.current_class:
                    updated_fee.class_level = updated_fee.student.current_class
                
                updated_fee.save()
                messages.success(request, f'Fee for {updated_fee.student.full_name} has been updated successfully!')
                return redirect('fee_detail', fee_id=updated_fee.id)
            except Exception as e:
                print(f"Error updating fee: {e}")
                messages.error(request, f'Error updating fee: {str(e)}')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeeForm(instance=fee)
        # Pre-populate the student and class_level fields
        form.initial['student'] = fee.student.id
        if fee.student.current_class:
            form.initial['class_level'] = fee.student.current_class.id
    
    context = {
        'form': form,
        'fee': fee,
    }
    return render(request, 'finances/fees/edit_fee.html', context)

@admin_required
def delete_fee(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    
    if request.method == 'POST':
        fee_name = fee.name
        fee.delete()
        messages.success(request, f'Fee "{fee_name}" has been deleted successfully!')
        return redirect('all_fees')
    
    context = {
        'fee': fee
    }
    return render(request, 'finances/fees/confirm_delete_fee.html', context)

@login_required
def buttons(request):
    return render(request, 'ui_elements/buttons.html')

@login_required
def modals(request):
    return render(request, 'ui_elements/modals.html')

@login_required_custom
def messaging(request):
    """Main messaging view"""
    if request.method == 'POST':
        try:
            receiver_id = request.POST.get('receiver')
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            
            if not receiver_id:
                messages.error(request, 'Please select a recipient.')
                return redirect('messaging')
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            receiver = User.objects.get(id=receiver_id)
            
            # Create message with file handling
            message = Message(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                content=content
            )
            
            # Handle file upload - Check both possible field names
            if 'attachments' in request.FILES:
                message.file = request.FILES.getlist('attachments')[0] # Get first file if multiple
            elif 'message_file' in request.FILES:
                message.file = request.FILES['message_file']
            
            message.save()
            
            messages.success(request, 'Message sent successfully!')
            return redirect('messaging')
            
        except User.DoesNotExist:
            messages.error(request, 'Selected recipient does not exist.')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
    
    # Get conversations logic
    from core.utils import get_conversations
    conversations = get_conversations(request.user)
    
    # Get message counts for the dashboard cards
    sent_count = Message.objects.filter(sender=request.user).count()
    received_count = Message.objects.filter(receiver=request.user).count()
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    context = {
        'users': User.objects.exclude(id=request.user.id),
        'conversations': conversations,
        'sent_count': sent_count,
        'received_count': received_count,
        'unread_count': unread_count,
    }
    return render(request, 'messaging/messaging.html', context)

@login_required
@require_POST
@csrf_exempt
def send_message_ajax(request):
    """AJAX view to send a message with file upload support - FIXED TIME FORMAT"""
    try:
        print(f"DEBUG: AJAX request received - Content-Type: {request.content_type}")
        print(f"DEBUG: POST data: {dict(request.POST)}")
        print(f"DEBUG: FILES data: {dict(request.FILES)}")
        
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content', '').strip()
        
        print(f"DEBUG: receiver_id: {receiver_id}, content: {content}")
        
        # Validate required fields
        if not receiver_id:
            return JsonResponse({
                'success': False,
                'error': 'Receiver ID is required'
            }, status=400)
        
        # Validate receiver exists
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Receiver user does not exist'
            }, status=400)
        
        # Create message
        message = Message(
            sender=request.user,
            receiver=receiver,
            subject='',  # Empty subject for simple messages
            content=content
        )
        
        # Handle file uploads - support multiple file field names
        files = request.FILES.getlist('file') or request.FILES.getlist('attachments')
        
        # For now, we'll only use the first file (model only supports one)
        if files:
            uploaded_file = files[0]  # Take the first file
            print(f"DEBUG: File uploaded - Name: {uploaded_file.name}, Size: {uploaded_file.size}")
            
            # Optional: Validate file size (e.g., 10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
                return JsonResponse({
                    'success': False,
                    'error': 'File size must be less than 10MB'
                }, status=400)
            
            message.file = uploaded_file
        
        message.save()
        print(f"DEBUG: Message saved with ID: {message.id}")
        print(f"DEBUG: Message sent_date: {message.sent_date}")
        print(f"DEBUG: Message sent_date ISO: {message.sent_date.isoformat()}")
        
        response_data = {
            'success': True,
            'message': 'Message sent successfully!',
            'message_id': message.id,
            'sent_date': message.sent_date.isoformat(),  # Use ISO format for consistency
            'sent_date_display': message.sent_date.strftime('%Y-%m-%d %H:%M:%S')  # Human readable format
        }
        
        # Add file info if file was uploaded
        if message.file:
            file_name = os.path.basename(message.file.name)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                # Fallback for common file types
                extension_to_type = {
                    '.pdf': 'application/pdf',
                    '.doc': 'application/msword',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    '.ppt': 'application/vnd.ms-powerpoint',
                    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    '.txt': 'text/plain',
                    '.zip': 'application/zip',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.mp4': 'video/mp4',
                    '.avi': 'video/x-msvideo',
                }
                content_type = extension_to_type.get(file_extension, 'application/octet-stream')
            
            response_data['file_info'] = {
                'name': file_name,
                'url': message.file.url,
                'file_type': content_type,
                'file_size': message.file.size
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"DEBUG: Error in send_message_ajax: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@login_required
@require_GET
def get_conversations_ajax(request):
    """AJAX view to get conversations for the current user"""
    try:
        from core.utils import get_conversations
        conversations_data = get_conversations(request.user)
        
        # Format conversations for JSON response
        formatted_conversations = []
        for conversation in conversations_data:
            user = conversation['user']
            latest_message = conversation['latest_message']
            
            # Build conversation data
            conv_data = {
                'user': {
                    'id': user.id,
                    'name': user.get_full_name() or user.username,
                    'username': user.username,
                },
                'user_type': conversation['user_type'],
                'is_online': conversation['is_online'],
                'unread_count': conversation['unread_count'],
                'latest_message': None,
            }
            
            # Add latest message data if exists
            if latest_message:
                conv_data['latest_message'] = {
                    'content': latest_message.content,
                    'sent_date': latest_message.sent_date.isoformat(),
                    'has_file': bool(latest_message.file),
                }
                
                # Add file information if message has a file
                if latest_message.file:
                    import os
                    file_name = os.path.basename(latest_message.file.name)
                    conv_data['latest_message']['file_name'] = file_name
                    conv_data['latest_message']['file_info'] = {
                        'name': file_name,
                        'url': latest_message.file.url,
                    }
            
            formatted_conversations.append(conv_data)
        
        return JsonResponse({
            'success': True,
            'conversations': formatted_conversations
        })
        
    except Exception as e:
        print(f"ERROR in get_conversations_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# def get_conversations(user):
#     """
#     Get all conversations for a user with the latest message and unread count
#     """
#     try:
#         # Get all users that the current user has messaged with
#         sent_to_users = Message.objects.filter(sender=user).values_list('receiver', flat=True).distinct()
#         received_from_users = Message.objects.filter(receiver=user).values_list('sender', flat=True).distinct()
        
#         # Combine and get unique user IDs
#         all_user_ids = set(list(sent_to_users) + list(received_from_users))
        
#         conversations_data = []
        
#         for user_id in all_user_ids:
#             try:
#                 other_user = User.objects.get(id=user_id)
                
#                 # Get the latest message in this conversation
#                 latest_message = Message.objects.filter(
#                     Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user)
#                 ).order_by('-sent_date').first()
                
#                 # Get unread count
#                 unread_count = Message.objects.filter(
#                     sender=other_user,
#                     receiver=user,
#                     is_read=False
#                 ).count()
                
#                 # Determine user type
#                 user_type = "USER"
#                 if hasattr(other_user, 'teacher') and other_user.teacher:
#                     user_type = "TEACHER"
#                 elif hasattr(other_user, 'student') and other_user.student:
#                     user_type = "STUDENT"
#                 elif hasattr(other_user, 'parent') and other_user.parent:
#                     user_type = "PARENT"
#                 elif other_user.is_staff:
#                     user_type = "STAFF"
                
#                 conversations_data.append({
#                     'user': other_user,
#                     'user_type': user_type,
#                     'latest_message': latest_message,
#                     'unread_count': unread_count,
#                     'is_online': False  # You can implement online status logic here
#                 })
                
#             except User.DoesNotExist:
#                 continue
        
#         # Sort by latest message date (most recent first)
#         conversations_data.sort(
#             key=lambda x: x['latest_message'].sent_date if x['latest_message'] else datetime.min, 
#             reverse=True
#         )
        
#         return conversations_data
        
#     except Exception as e:
#         logger.error(f"Error in get_conversations: {str(e)}")
#         return []

@login_required
@require_POST
def mark_all_read(request):
    """Mark all messages as read for the current user"""
    try:
        # Mark all received messages as read
        updated_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Marked {updated_count} messages as read',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

import mimetypes
import os

@login_required_custom
@require_GET
def get_conversation_messages(request, user_id):
    """AJAX view to get messages for a specific conversation - FIXED VERSION"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = get_object_or_404(User, id=user_id)
        
        # Get messages between current user and the other user
        messages_qs = Message.objects.filter(
            Q(sender=request.user, receiver=other_user) | 
            Q(sender=other_user, receiver=request.user)
        ).order_by('sent_date')
        
        # Mark received messages as read
        Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)
        
        messages_data = []
        for msg in messages_qs:
            message_data = {
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_name': msg.sender.get_full_name() or msg.sender.username,
                'content': msg.content,
                'subject': msg.subject,
                'sent_date': msg.sent_date.isoformat(),
                'is_read': msg.is_read,
                'is_outgoing': msg.sender.id == request.user.id,
            }
            
            # FIXED: Handle file information properly
            if msg.file:
                file_name = os.path.basename(msg.file.name)
                file_extension = os.path.splitext(file_name)[1].lower()
                
                # Determine content type using mimetypes
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    # Fallback for common file types
                    extension_to_type = {
                        '.pdf': 'application/pdf',
                        '.doc': 'application/msword',
                        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        '.xls': 'application/vnd.ms-excel',
                        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        '.ppt': 'application/vnd.ms-powerpoint',
                        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                        '.txt': 'text/plain',
                        '.zip': 'application/zip',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.mp4': 'video/mp4',
                        '.avi': 'video/x-msvideo',
                    }
                    content_type = extension_to_type.get(file_extension, 'application/octet-stream')
                
                message_data['file_info'] = {
                    'url': msg.file.url,
                    'name': file_name,
                    'file_type': content_type,
                    'file_size': msg.file.size
                }
            
            messages_data.append(message_data)
        
        # Check if user is online
        from core.utils import check_user_online, get_user_type
        is_online = check_user_online(other_user)
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'other_user': {
                'id': other_user.id,
                'name': other_user.get_full_name() or other_user.username,
                'type': get_user_type(other_user),
                'is_online': is_online,
            }
        })
        
    except Exception as e:
        print(f"ERROR in get_conversation_messages: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'Error loading messages: {str(e)}'
        }, status=500)

@login_required
def download_message_file(request, message_id):
    """Download a file attached to a message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to access this file
    if request.user != message.sender and request.user != message.receiver:
        raise PermissionDenied("You don't have permission to access this file.")
    
    if not message.file:
        raise Http404("File not found.")
    
    # Serve the file for download
    response = FileResponse(message.file.open(), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{message.file.name.split("/")[-1]}"'
    return response

@login_required
def get_user_type(user):
    """Helper function to get user type"""
    try:
        if hasattr(user, 'teacher'):
            return 'TEACHER'
        elif hasattr(user, 'student'):
            return 'STUDENT'
        elif hasattr(user, 'parent'):
            return 'PARENT'
        elif user.is_staff:
            return 'STAFF'
        return 'USER'
    except:
        return 'USER'

@login_required
def notice_board(request):
    # Get today's date for active notice filtering
    today = timezone.now().date()
    
    # Filter notices based on user role
    if request.user.is_staff:
        # Staff can see all notices
        notices = Notice.objects.all().order_by('-publish_date')
    elif hasattr(request.user, 'teacher'):
        # Teachers can see teacher notices and general notices
        notices = Notice.objects.filter(
            target_audience__in=['ALL', 'TEACHERS']
        ).order_by('-publish_date')
    elif hasattr(request.user, 'student'):
        # Students can see student notices and general notices
        notices = Notice.objects.filter(
            target_audience__in=['ALL', 'STUDENTS']
        ).order_by('-publish_date')
    elif hasattr(request.user, 'parent'):
        # Parents can see parent notices and general notices
        notices = Notice.objects.filter(
            target_audience__in=['ALL', 'PARENTS']
        ).order_by('-publish_date')
    else:
        # Default users can only see general notices
        notices = Notice.objects.filter(target_audience='ALL').order_by('-publish_date')
    
    # Check for active-only filter
    active_only = request.GET.get('active') == 'true'
    if active_only:
        notices = notices.filter(
            expiry_date__isnull=True
        ) | notices.filter(
            expiry_date__gte=today
        )
    
    # Calculate statistics (for staff only)
    if request.user.is_staff:
        active_notices_count = Notice.objects.filter(
            expiry_date__isnull=True
        ).count() + Notice.objects.filter(
            expiry_date__gte=today
        ).count()
        high_priority_count = Notice.objects.filter(priority='HIGH').count()
    else:
        active_notices_count = None
        high_priority_count = None
    
    context = {
        'notices': notices,
        'active_notices_count': active_notices_count,
        'high_priority_count': high_priority_count,
    }
    
    return render(request, 'notice/notice_board.html', context)

@login_required
def account_settings(request):
    if request.method == 'POST':
        try:
            user = request.user
            action = request.POST.get('action', 'update_profile')

            # ── Password change ──────────────────────────────────────────────
            if action == 'change_password':
                from django.contrib.auth import update_session_auth_hash
                current_password = request.POST.get('current_password', '')
                new_password = request.POST.get('new_password', '')
                confirm_password = request.POST.get('confirm_password', '')

                if not user.check_password(current_password):
                    messages.error(request, 'Current password is incorrect.')
                elif len(new_password) < 8:
                    messages.error(request, 'New password must be at least 8 characters.')
                elif new_password != confirm_password:
                    messages.error(request, 'New passwords do not match.')
                else:
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)  # keep user logged in
                    messages.success(request, 'Password changed successfully!')
                return redirect('account_settings')

            # ── Profile / contact update ─────────────────────────────────────
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()

            if hasattr(user, 'teacher') and user.teacher:
                teacher = user.teacher
                teacher.phone = request.POST.get('phone', teacher.phone)
                teacher.address = request.POST.get('address', teacher.address)
                if 'photo' in request.FILES:
                    teacher.photo = request.FILES['photo']
                teacher.save()

            elif hasattr(user, 'student') and user.student:
                student = user.student
                student.phone = request.POST.get('phone', student.phone)
                student.address = request.POST.get('address', student.address)
                # Only update guardian_email if a non-empty value was submitted
                submitted_alt_email = request.POST.get('alt_email', '').strip()
                if submitted_alt_email:
                    student.guardian_email = submitted_alt_email
                if 'photo' in request.FILES:
                    student.photo = request.FILES['photo']
                student.save()

            elif hasattr(user, 'parent') and user.parent:
                parent = user.parent
                parent.phone = request.POST.get('phone', parent.phone)
                parent.address = request.POST.get('address', parent.address)
                parent.email = request.POST.get('email', parent.email)
                if 'photo' in request.FILES:
                    parent.photo = request.FILES['photo']
                parent.save()

            messages.success(request, 'Account settings updated successfully!')
            return redirect('account_settings')

        except Exception as e:
            messages.error(request, f'Error updating account: {str(e)}')

    return render(request, 'account/account_settings.html')

# AJAX views
@login_required
def get_sections_by_class(request, class_id):
    sections = Section.objects.filter(class_name_id=class_id).values('id', 'name')
    return JsonResponse(list(sections), safe=False)

@login_required
def check_username_availability(request):
    username = request.GET.get('username')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'available': not exists})

@login_required
def check_email_availability(request):
    email = request.GET.get('email')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'available': not exists})

@admin_required
def create_notice_ajax(request):
    if request.method == 'POST' and request.user.is_staff:
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            priority = request.POST.get('priority', 'MEDIUM')
            target_audience = request.POST.get('target_audience', 'ALL')
            expiry_date = request.POST.get('expiry_date') or None
            
            notice = Notice.objects.create(
                title=title,
                content=content,
                priority=priority,
                target_audience=target_audience,
                expiry_date=expiry_date,
                posted_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Notice created successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })

@admin_required
def update_notice_ajax(request):
    if request.method == 'POST' and request.user.is_staff:
        try:
            notice_id = request.POST.get('notice_id')
            notice = Notice.objects.get(id=notice_id, posted_by=request.user)
            
            notice.title = request.POST.get('title')
            notice.content = request.POST.get('content')
            notice.priority = request.POST.get('priority')
            notice.target_audience = request.POST.get('target_audience')
            notice.expiry_date = request.POST.get('expiry_date') or None
            notice.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Notice updated successfully!'
            })
        except Notice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Notice not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })

@admin_required
def delete_notice_ajax(request):
    if request.method == 'POST' and request.user.is_staff:
        try:
            notice_id = request.POST.get('notice_id')
            notice = Notice.objects.get(id=notice_id, posted_by=request.user)
            notice.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Notice deleted successfully!'
            })
        except Notice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Notice not found'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })

@admin_required
def all_parents(request):
    parents = Parent.objects.all().order_by('first_name', 'last_name')
    
    search_query = request.GET.get('search')
    if search_query:
        parents = parents.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    context = {
        'parents': parents,
    }
    return render(request, 'parents/all_parents.html', context)

@login_required
def parent_details(request, parent_id):
    parent = get_object_or_404(Parent, id=parent_id)
    children = parent.students.all()
    
    
    
    total_unpaid = Fee.objects.filter(student__in=children, status='unpaid').aggregate(total=Sum('amount'))['total'] or 0
    total_paid = Fee.objects.filter(student__in=children, status='paid').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'parent': parent,
        'children': children,
        'total_unpaid': total_unpaid,
        'total_paid': total_paid,
    }
    return render(request, 'parents/parent_details.html', context)

@admin_required
def add_parent_with_students(request):
    """Add parent with option to add students in one form"""
    
    if request.method == 'POST':
        try:
            current_step = request.POST.get('current_step', '1')
            
            if current_step == '3':  # Final submission
                # Step 1: Create parent
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password1')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                phone = request.POST.get('phone')
                address = request.POST.get('address', '')
                occupation = request.POST.get('occupation', '')
                father_name = request.POST.get('father_name', '')
                mother_name = request.POST.get('mother_name', '')
                
                # Validate required fields
                required_fields = ['username', 'email', 'password1', 'first_name', 'last_name', 'phone']
                for field in required_fields:
                    if not request.POST.get(field):
                        messages.error(request, f'Missing required field: {field}')
                        return redirect('add_parent_with_students')
                
                # Check if username exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists.')
                    return redirect('add_parent_with_students')
                
                # Check if email exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'Email already exists.')
                    return redirect('add_parent_with_students')
                
                # Create parent user
                parent_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Add to Parent group
                from django.contrib.auth.models import Group
                parent_group, created = Group.objects.get_or_create(name='Parent')
                parent_user.groups.add(parent_group)
                
                # Create parent profile
                parent = Parent.objects.create(
                    user=parent_user,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    email=email,
                    address=address,
                    occupation=occupation,
                    father_name=father_name,
                    mother_name=mother_name,
                )
                
                # Step 2: Link existing students if provided
                existing_student_ids = request.POST.getlist('existing_students')
                if existing_student_ids:
                    students = Student.objects.filter(id__in=existing_student_ids, is_active=True)
                    linked_count = 0
                    
                    for student in students:
                        # Check if student is already linked to this parent (avoid duplicates)
                        if not parent.students.filter(id=student.id).exists():
                            parent.students.add(student)
                            linked_count += 1
                            # Update student's parent info
                            student.father_name = father_name
                            student.mother_name = mother_name
                            student.guardian_email = email
                            student.guardian_phone = phone
                            student.address = address
                            student.save()
                    
                    if linked_count > 0:
                        messages.success(request, f'Successfully linked {linked_count} existing student(s).')
                
                # Step 3: Create new students if enabled
                add_students = request.POST.get('add_students') == 'on'
                created_students = []
                
                if add_students:
                    student_index = 0
                    
                    while f'students[{student_index}][first_name]' in request.POST:
                        student_first_name = request.POST.get(f'students[{student_index}][first_name]', '').strip()
                        student_last_name = request.POST.get(f'students[{student_index}][last_name]', '').strip()
                        date_of_birth = request.POST.get(f'students[{student_index}][date_of_birth]')
                        gender = request.POST.get(f'students[{student_index}][gender]')
                        class_level_id = request.POST.get(f'students[{student_index}][class_level]')
                        section_id = request.POST.get(f'students[{student_index}][section]')
                        medical_conditions = request.POST.get(f'students[{student_index}][medical_conditions]', '')
                        
                        # Only create student if we have required fields
                        if all([student_first_name, student_last_name, date_of_birth, gender, class_level_id]):
                            try:
                                # Generate student ID - SAME AS admit_form
                                year = timezone.now().year
                                last_student = Student.objects.filter(admission_date__year=year).order_by('-id').first()
                                if last_student:
                                    last_id = int(last_student.student_id.split('-')[-1])
                                    new_id = last_id + 1
                                else:
                                    new_id = 1
                                student_id = f"STU-{year}-{new_id:04d}"
                                
                                # Generate roll number - EXACTLY LIKE admit_form
                                roll_number = f"RN{new_id:03d}"
                                
                                # Get class and section objects
                                class_level = Class.objects.get(id=class_level_id)
                                section = Section.objects.get(id=section_id) if section_id else None
                                
                                # Create student - SAME FIELDS AS admit_form
                                student = Student.objects.create(
                                    # Student Information
                                    student_id=student_id,
                                    first_name=student_first_name,
                                    last_name=student_last_name,
                                    gender=gender,
                                    date_of_birth=date_of_birth,
                                    roll_number=roll_number,
                                    admission_date=timezone.now().date(),
                                    
                                    # Contact Information
                                    address=address,
                                    phone=phone,
                                    email=email,
                                    
                                    # Academic Information
                                    current_class=class_level,
                                    current_section=section,
                                    
                                    # Parent Information
                                    father_name=father_name,
                                    mother_name=mother_name,
                                    guardian_email=email,
                                    guardian_phone=phone,
                                    
                                    # Emergency Contact
                                    emergency_contact_name=f"{first_name} {last_name}",
                                    emergency_contact_phone=phone,
                                    emergency_relationship="Parent",
                                    
                                    # Medical Information
                                    medical_conditions=medical_conditions,
                                    
                                    # Optional Fields from admit_form
                                    father_occupation=occupation,
                                    mother_occupation=occupation,
                                    # Add other optional fields if needed:
                                    # national_id=request.POST.get(f'students[{student_index}][national_id]', '').strip(),
                                    # previous_school=request.POST.get(f'students[{student_index}][previous_school]', '').strip(),
                                    # transfer_certificate_no=request.POST.get(f'students[{student_index}][transfer_certificate_no]', '').strip(),
                                    # medications=request.POST.get(f'students[{student_index}][medications]', '').strip(),
                                    # doctor_name=request.POST.get(f'students[{student_index}][doctor_name]', '').strip(),
                                    # doctor_phone=request.POST.get(f'students[{student_index}][doctor_phone]', '').strip(),
                                )
                                
                                # Handle student photo if needed
                                # if f'students[{student_index}][photo]' in request.FILES:
                                #     student.photo = request.FILES[f'students[{student_index}][photo]']
                                #     student.save()
                                
                                # Link to parent
                                parent.students.add(student)
                                created_students.append(student)
                                
                                messages.success(request, f'Student {student_first_name} {student_last_name} created with ID: {student_id}, Roll: {roll_number}')
                                
                            except Exception as e:
                                messages.warning(request, f'Error creating student {student_first_name} {student_last_name}: {str(e)}')
                                import traceback
                                traceback.print_exc()
                        
                        student_index += 1
                    
                    if created_students:
                        messages.success(request, f'Created {len(created_students)} new student(s).')
                
                # Success messages
                total_students = parent.students.count()
                messages.success(request, f'✅ Parent {parent.full_name} created successfully!')
                
                if total_students > 0:
                    messages.success(request, f'📚 {total_students} student(s) linked to parent.')
                
                messages.info(request, f'🔑 Parent login credentials:')
                messages.info(request, f'   Username: <strong>{username}</strong>')
                messages.info(request, f'   Password: <strong>{password}</strong>')
                
                return redirect('parent_details', parent_id=parent.id)
            
            else:
                # If not final step, reload with current step
                messages.info(request, 'Please complete all steps to submit.')
                return redirect('add_parent_with_students')
                
        except Exception as e:
            messages.error(request, f'Error creating parent: {str(e)}')
            import traceback
            traceback.print_exc()
            return redirect('add_parent_with_students')
    
    # GET request - show form with initial data
    # Get students that are not linked to any parent
    students = Student.objects.filter(is_active=True)
    
    # Get students without parents (if there's a ManyToManyField)
    try:
        # Try to filter students without parents
        students_without_parents = students.filter(parents__isnull=True)
    except:
        # If the above doesn't work, get all active students
        students_without_parents = students
    
    classes = Class.objects.all().order_by('name')
    sections = Section.objects.all().order_by('name')
    
    context = {
        'students': students_without_parents,
        'classes': classes,
        'sections': sections,
    }
    
    return render(request, 'parents/add_parent.html', context)

@admin_required
def add_parent(request):
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'password1', 'first_name', 'last_name', 'phone']
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f'Missing required field: {field}')
                    return render(request, 'parents/add_parent.html', {
                        'students': Student.objects.filter(is_active=True),
                        'form_data': request.POST
                    })
            
            # Check if username already exists
            if User.objects.filter(username=request.POST['username']).exists():
                messages.error(request, 'Username already exists. Please choose a different one.')
                return render(request, 'parents/add_parent.html', {
                    'students': Student.objects.filter(is_active=True),
                    'form_data': request.POST
                })
            
            # Check if email already exists
            if User.objects.filter(email=request.POST['email']).exists():
                messages.error(request, 'Email already exists. Please use a different email.')
                return render(request, 'parents/add_parent.html', {
                    'students': Student.objects.filter(is_active=True),
                    'form_data': request.POST
                })
            
            # Create parent user
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password1']
            
            parent_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name']
            )
            
            # Add to Parent group
            from django.contrib.auth.models import Group
            parent_group, created = Group.objects.get_or_create(name='Parent')
            parent_user.groups.add(parent_group)
            
            # Create parent profile
            parent = Parent.objects.create(
                user=parent_user,
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                phone=request.POST['phone'],
                email=email,
                address=request.POST.get('address', ''),
                occupation=request.POST.get('occupation', ''),
                father_name=request.POST.get('father_name', ''),
                mother_name=request.POST.get('mother_name', ''),
                photo=request.FILES.get('photo'),
            )
            
            # Link existing students if provided
            student_ids = request.POST.getlist('students')
            if student_ids:
                try:
                    students = Student.objects.filter(id__in=student_ids, is_active=True)
                    linked_students_count = 0
                    
                    for student in students:
                        # Check if student is already linked to another parent
                        existing_parents = Parent.objects.filter(students=student)
                        if not existing_parents.exists():
                            parent.students.add(student)
                            linked_students_count += 1
                            # Update student's parent information
                            student.father_name = parent.father_name or request.POST.get('father_name', '')
                            student.mother_name = parent.mother_name or request.POST.get('mother_name', '')
                            student.guardian_email = parent.email
                            student.guardian_phone = parent.phone
                            student.save()
                        else:
                            messages.warning(request, f'Student {student.full_name} is already linked to another parent.')
                    
                    if linked_students_count > 0:
                        parent.save()
                        messages.success(request, f'Successfully linked {linked_students_count} student(s) to parent.')
                
                except Exception as e:
                    # Continue even if student linking fails - parent is already created
                    messages.warning(request, f'Parent created but error linking students: {str(e)}')
            
            messages.success(request, f'Parent {parent.full_name} added successfully!')
            messages.info(request, f'Parent login created:<br>Username: {username}<br>Password: {password}')
            
            # Send email notification (optional)
            try:
                send_mail(
                    f'Parent Account Created - {parent.full_name}',
                    f'''Dear {parent.first_name},

Your parent account has been created successfully.

Login Details:
Username: {username}
Password: {password}

Please change your password after first login.

Best regards,
School Administration''',
                    'noreply@petra.edu',
                    [parent.email],
                    fail_silently=True,
                )
                messages.info(request, 'Account details emailed to parent.')
            except Exception as e:
                print(f"Email sending failed: {e}")
            
            return redirect('parent_details', parent_id=parent.id)
            
        except Exception as e:
            messages.error(request, f'Error adding parent: {str(e)}')
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error adding parent: {str(e)}', exc_info=True)
    
    # GET request - show form
    students = Student.objects.filter(is_active=True).select_related('current_class')
    context = {
        'students': students,
    }
    return render(request, 'parents/add_parent.html', context)

@admin_required
def add_student_to_parent(request, parent_id):
    """Add a new student for an existing parent"""
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        try:
            # Extract student data
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            date_of_birth = request.POST.get('date_of_birth')
            gender = request.POST.get('gender')
            class_level_id = request.POST.get('class_level')
            section_id = request.POST.get('section')
            
            # Parent information (use existing parent data)
            father_name = parent.father_name or request.POST.get('father_name', '').strip()
            mother_name = parent.mother_name or request.POST.get('mother_name', '').strip()
            
            # Validate required fields
            if not all([first_name, last_name, date_of_birth, gender, class_level_id]):
                messages.error(request, 'Please fill in all required fields.')
                classes = Class.objects.all().order_by('name')
                sections = Section.objects.all().order_by('name')
                return render(request, 'parents/add_student_to_parent.html', {
                    'parent': parent,
                    'classes': classes,
                    'sections': sections
                })
            
            # Get class and section objects
            class_level = get_object_or_404(Class, id=class_level_id)
            section = get_object_or_404(Section, id=section_id) if section_id else None
            
            # Generate student ID and roll number
            year = timezone.now().year
            last_student = Student.objects.filter(admission_date__year=year).order_by('-id').first()
            if last_student:
                last_id = int(last_student.student_id.split('-')[-1])
                new_id = last_id + 1
            else:
                new_id = 1
            student_id = f"STU-{year}-{new_id:04d}"
            
            # Generate roll number
            roll_number = f"RN{new_id:03d}"
            
            # Create student user (optional - can be created later)
            student_user = None
            try:
                student_username = student_id.lower()
                student_user = User.objects.create_user(
                    username=student_username,
                    password='student123',  # Default password
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{student_username}@petra.edu"
                )
                
                # Add student to Student group
                from django.contrib.auth.models import Group
                student_group, created = Group.objects.get_or_create(name='Student')
                student_user.groups.add(student_group)
                
            except Exception as e:
                print(f"DEBUG: Could not create student user: {e}")
                # Continue without user - it can be created later
            
            # Create student profile
            student = Student.objects.create(
                user=student_user,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                address=parent.address,  # Use parent's address
                phone=parent.phone,      # Use parent's phone
                email=parent.email,      # Use parent's email
                current_class=class_level,
                current_section=section,
                roll_number=roll_number,
                admission_date=timezone.now().date(),
                # Parent information
                father_name=father_name,
                father_occupation=parent.occupation or '',
                mother_name=mother_name,
                mother_occupation=parent.occupation or '',
                guardian_email=parent.email,
                guardian_phone=parent.phone,
                # Emergency contact (use parent as emergency contact)
                emergency_contact_name=f"{parent.first_name} {parent.last_name}",
                emergency_contact_phone=parent.phone,
                emergency_relationship="Parent",
                # Medical information
                medical_conditions=request.POST.get('medical_conditions', '').strip(),
                medications=request.POST.get('medications', '').strip(),
                doctor_name=request.POST.get('doctor_name', '').strip(),
                doctor_phone=request.POST.get('doctor_phone', '').strip(),
                # National ID
                national_id=request.POST.get('national_id', '').strip(),
            )
            
            # Handle photo upload
            if 'student_photo' in request.FILES:
                student.photo = request.FILES['student_photo']
                student.save()
            
            # Link student to parent
            parent.students.add(student)
            
            messages.success(request, f'Student {first_name} {last_name} added successfully and linked to {parent.full_name}!')
            messages.info(request, f'Student ID: {student_id}, Roll Number: {roll_number}')
            
            if student_user:
                messages.info(request, f'Student login created: Username: {student_username}, Password: student123')
            
            return redirect('parent_details', parent_id=parent.id)
            
        except Exception as e:
            print(f"Error adding student to parent: {e}")
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'Error adding student: {str(e)}')
    
    # GET request - show form
    classes = Class.objects.all().order_by('name')
    sections = Section.objects.all().order_by('name')
    
    context = {
        'parent': parent,
        'classes': classes,
        'sections': sections,
    }
    
    return render(request, 'parents/add_student_to_parent.html', context)


# Add these missing views to your views.py file

@admin_required
def export_results_csv(request, exam_id):
    """Export exam results to CSV format"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('position')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{exam.name}_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Position', 'Student ID', 'Student Name', 'Roll Number', 'Marks Obtained', 'Total Marks', 'Percentage', 'Grade', 'Remarks'])
    
    for result in results:
        percentage = (float(result.marks_obtained) / float(exam.total_marks)) * 100
        writer.writerow([
            result.position,
            result.student.student_id,
            result.student.full_name,
            result.student.roll_number,
            float(result.marks_obtained),
            float(exam.total_marks),
            round(percentage, 2),
            result.grade,
            result.remarks or ''
        ])
    
    return response

def manage_classes(request):
    """View to manage classes with subjects - Simple approach"""
    # Get all classes
    classes = Class.objects.select_related('class_teacher').prefetch_related(
        'section_set',
        'students'
    ).order_by('level_category', 'grade_level')

    # Search functionality (basic)
    search_query = request.GET.get('search', '')
    level_query = request.GET.get('level', '')

    if search_query:
        classes = classes.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    if level_query:
        classes = classes.filter(level_category=level_query)

    # Get subjects for each class using separate queries
    for class_obj in classes:
        # Get subjects from timetable
        timetable_subjects = list(Subject.objects.filter(
            timetable__class_level=class_obj
        ).distinct())
        
        # Get subjects from assignments
        assignment_subjects = list(Subject.objects.filter(
            assignment__class_level=class_obj
        ).distinct())
        
        # Combine subjects
        all_subjects = timetable_subjects + assignment_subjects
        # Remove duplicates by converting to set and back to list
        class_obj.subjects = list({subject.id: subject for subject in all_subjects}.values())
        
        # Get sections
        class_obj.sections_list = class_obj.section_set.all()

    # Handle subject search in Python (if needed)
    subject_query = request.GET.get('subject', '')
    if subject_query:
        classes = [cls for cls in classes if any(
            subject_query.lower() in subject.name.lower() 
            for subject in cls.subjects
        )]

    # Statistics
    total_classes = Class.objects.count()
    total_subjects = Subject.objects.count()
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()

    context = {
        'classes': classes,
        'total_classes': total_classes,
        'total_subjects': total_subjects,
        'total_students': total_students,
        'total_teachers': total_teachers,
    }

    return render(request, 'academic/manage_classes.html', context)


@admin_required
def add_class(request):
    """Add a new class"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class "{class_obj.name}" created successfully!')
            return redirect('manage_classes')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClassForm()
    
    # Get common codes from existing classes with their level categories
    common_classes = Class.objects.values('code', 'level_category').distinct()[:10]
    common_codes = [(cls['code'], cls['level_category']) for cls in common_classes]
    
    # If no existing classes, provide some sensible defaults
    if not common_codes:
        common_codes = [
            ('PP1', 'ECDE'),
            ('PP2', 'ECDE'),
            ('1', 'PRIMARY'),
            ('2', 'PRIMARY'),
            ('3', 'PRIMARY'),
            ('4', 'PRIMARY'),
            ('5', 'PRIMARY'),
            ('6', 'PRIMARY'),
            ('7', 'JUNIOR_SECONDARY'),
            ('8', 'JUNIOR_SECONDARY'),
            ('9', 'JUNIOR_SECONDARY'),
        ]
    
    context = {
        'form': form,
        'common_codes': common_codes,
        'title': 'Add New Class'
    }
    return render(request, 'academic/class_form.html', context)

@admin_required
def edit_class(request, class_id):
    """Edit an existing class"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Class "{class_obj.name}" updated successfully!')
            return redirect('manage_classes')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClassForm(instance=class_obj)
    
    # Get common codes from existing classes
    common_codes = Class.objects.values_list('code', flat=True).distinct()[:10]
    
    context = {
        'form': form,
        'class_obj': class_obj,
        'common_codes': common_codes,
        'title': f'Edit {class_obj.name}'
    }
    return render(request, 'academic/class_form.html', context)

@admin_required
def view_class(request, class_id):
    """View class details"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    # Get related data
    sections = class_obj.section_set.all()
    students = class_obj.students.filter(is_active=True)
    class_subjects = class_obj.class_subjects.all()
    timetables = class_obj.timetables.all()
    assignments = class_obj.assignments.all()
    
    # Get subjects from timetable and assignments (same approach as manage_classes)
    timetable_subjects = list(Subject.objects.filter(
        timetable__class_level=class_obj
    ).distinct())
    
    assignment_subjects = list(Subject.objects.filter(
        assignment__class_level=class_obj
    ).distinct())
    
    # Combine subjects and remove duplicates
    all_subjects = timetable_subjects + assignment_subjects
    all_subjects = list({subject.id: subject for subject in all_subjects}.values())
    
    # Get statistics
    total_students = students.count()
    total_sections = sections.count()
    total_subjects = len(all_subjects)
    total_assignments = assignments.count()
    total_timetable_entries = timetables.count()
    
    context = {
        'class_obj': class_obj,
        'sections': sections,
        'students': students[:10],  # Show first 10 students
        'all_students_count': total_students,
        'class_subjects': class_subjects,
        'all_subjects': all_subjects,
        'timetables': timetables,
        'assignments': assignments[:10],  # Show first 10 assignments
        'total_students': total_students,
        'total_sections': total_sections,
        'total_subjects': total_subjects,
        'total_assignments': assignments.count(),
        'total_timetable_entries': total_timetable_entries,
    }
    return render(request, 'academic/class_details.html', context)

@admin_required
def delete_class(request, class_id):
    """Delete a class with cascade handling"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        class_name = class_obj.name
        
        # Get counts before deletion for message
        students_count = class_obj.students.count()
        sections_count = class_obj.section_set.count()
        class_subjects_count = class_obj.class_subjects.count()
        timetables_count = class_obj.timetables.count()
        assignments_count = class_obj.assignments.count()
        
        # Delete the class (cascade will handle related objects)
        class_obj.delete()
        
        # Build detailed success message
        deleted_items = []
        if sections_count > 0:
            deleted_items.append(f"{sections_count} section(s)")
        if class_subjects_count > 0:
            deleted_items.append(f"{class_subjects_count} class subject allocation(s)")
        if timetables_count > 0:
            deleted_items.append(f"{timetables_count} timetable entry/entries")
        if assignments_count > 0:
            deleted_items.append(f"{assignments_count} assignment(s)")
        if students_count > 0:
            deleted_items.append(f"{students_count} student(s) unlinked")
        
        if deleted_items:
            message = f'Class "{class_name}" deleted successfully! Also deleted/unlinked: {", ".join(deleted_items)}.'
        else:
            message = f'Class "{class_name}" deleted successfully!'
        
        messages.success(request, message)
        return redirect('manage_classes')
    
    # Get all related data for display
    sections = class_obj.section_set.all()
    students = class_obj.students.all()
    class_subjects = class_obj.class_subjects.all()
    timetables = class_obj.timetables.all()
    assignments = class_obj.assignments.all()
    
    # Count related objects
    related_counts = {
        'sections': sections.count(),
        'students': students.count(),
        'class_subjects': class_subjects.count(),
        'timetables': timetables.count(),
        'assignments': assignments.count(),
    }
    
    context = {
        'class_obj': class_obj,
        'sections': sections,
        'students': students,
        'class_subjects': class_subjects,
        'timetables': timetables,
        'assignments': assignments,
        'related_counts': related_counts,
    }
    return render(request, 'academic/confirm_delete_class.html', context)

@admin_required
def manage_subjects(request):
    """Manage subjects"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    # Get all subjects
    subjects = Subject.objects.all()
    
    # Get all teachers with their related user and subjects
    all_teachers = Teacher.objects.select_related('user').all()

    # Example: you can now access teacher.assigned_subjects.all() for each teacher

    context = {
        'subjects': subjects,
        'all_teachers': all_teachers,
        'title': 'Manage Subjects'
    }
    return render(request, 'academic/manage_subjects.html', context)


@admin_required
def add_subject(request):
    """Add a new subject"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" created successfully!')
            return redirect('manage_subjects')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm()
    
    context = {
        'form': form,
        'title': 'Add New Subject'
    }
    return render(request, 'academic/subject_form.html', context)

@admin_required
def edit_subject(request, subject_id):
    """Edit an existing subject"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject "{subject.name}" updated successfully!')
            return redirect('manage_subjects')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm(instance=subject)
    
    context = {
        'form': form,
        'title': 'Edit Subject',
        'subject': subject
    }
    return render(request, 'academic/subject_form.html', context)

@admin_required
def delete_subject(request, subject_id):
    """Delete a subject"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        subject_name = subject.name
        subject.delete()
        messages.success(request, f'Subject "{subject_name}" deleted successfully!')
        return redirect('manage_subjects')
    
    context = {
        'subject': subject
    }
    return render(request, 'academic/confirm_delete_subject.html', context)

@admin_required
def manage_timetable(request):
    """Main timetable management view"""
    classes = Class.objects.all()
    sections = Section.objects.all()
    subjects = Subject.objects.all()
    teachers = Teacher.objects.all()
    
    # Get filter parameters
    selected_class = request.GET.get('class')
    selected_section = request.GET.get('section')
    selected_teacher = request.GET.get('teacher')
    
    # Filter timetable entries
    timetable_entries = Timetable.objects.select_related(
        'class_level', 'section', 'subject', 'teacher'
    ).all()
    
    if selected_class:
        timetable_entries = timetable_entries.filter(class_level_id=selected_class)
    if selected_section:
        timetable_entries = timetable_entries.filter(section_id=selected_section)
    if selected_teacher:
        timetable_entries = timetable_entries.filter(teacher_id=selected_teacher)
    
    # Get unique periods and times
    periods_data = []
    if timetable_entries.exists():
        period_numbers = timetable_entries.values_list('period_number', flat=True).distinct().order_by('period_number')
        
        for period_num in period_numbers:
            period_entries = timetable_entries.filter(period_number=period_num)
            first_entry = period_entries.first()
            
            period_data = {
                'id': period_num,
                'period_number': period_num,
                'start_time': first_entry.start_time,
                'end_time': first_entry.end_time,
                'is_break': first_entry.is_break,
                'break_name': first_entry.break_name,
                'is_current': is_current_period(first_entry.start_time, first_entry.end_time),
            }
            
            # Add subjects for each day
            for day_code, day_name in Timetable.DAY_CHOICES:
                day_entry = period_entries.filter(day=day_code).first()
                if day_entry:
                    period_data[f'{day_code.lower()}_subject'] = day_entry.subject
                    period_data[f'{day_code.lower()}_teacher'] = day_entry.teacher
                    period_data[f'{day_code.lower()}_room'] = day_entry.room
                else:
                    period_data[f'{day_code.lower()}_subject'] = None
                    period_data[f'{day_code.lower()}_teacher'] = None
                    period_data[f'{day_code.lower()}_room'] = ''
            
            periods_data.append(period_data)
    else:
        # Use sample structure if no timetable exists
        periods_data = create_sample_periods_structure()
    
    # Calculate teacher workload
    teacher_workload = []
    for teacher in teachers:
        periods_count = Timetable.objects.filter(teacher=teacher).count()
        teacher_workload.append({
            'teacher': teacher,
            'periods_count': periods_count,
            'subjects': teacher.subjects.all()
        })
    
    context = {
        'classes': classes,
        'sections': sections,
        'subjects': subjects,
        'teachers': teachers,
        'periods': periods_data,
        'teacher_workload': teacher_workload,
        'selected_class': int(selected_class) if selected_class else None,
        'selected_section': int(selected_section) if selected_section else None,
        'selected_teacher': int(selected_teacher) if selected_teacher else None,
        'form': TimetableForm(),
        'current_week': timezone.now().isocalendar()[1],
    }
    return render(request, 'academic/manage_timetable.html', context)

@admin_required
@user_passes_test(lambda u: u.is_staff)
def generate_timetable_automatically(request):
    """Generate timetable automatically"""
    if request.method == 'POST':
        class_id = request.POST.get('class_level')
        section_id = request.POST.get('section')
        generator_type = request.POST.get('generator_type', 'basic')
        
        if not class_id or not section_id:
            messages.error(request, 'Please select both class and section')
            return redirect('manage_timetable')
        
        class_level = get_object_or_404(Class, id=class_id)
        section = get_object_or_404(Section, id=section_id)
        
        try:
            if generator_type == 'advanced':
                generator = AdvancedTimetableGenerator(class_level, section)
                success, message = generator.generate_optimized_timetable()
            else:
                generator = TimetableGenerator(class_level, section)
                success, message = generator.generate_timetable()
            
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
                
        except Exception as e:
            messages.error(request, f'Error generating timetable: {str(e)}')
    
    return redirect('manage_timetable')



@admin_required
def add_timetable_entry(request):
    """Add new timetable entry"""
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            timetable = form.save()
            messages.success(request, f'Timetable entry added successfully for {timetable.class_level.name}!')
            return redirect('manage_timetable')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TimetableForm()
    
    context = {
        'form': form,
        'title': 'Add Timetable Entry'
    }
    return render(request, 'academic/timetable_form.html', context)

@admin_required
def edit_timetable_entry(request, pk):
    """Edit existing timetable entry"""
    timetable = get_object_or_404(Timetable, pk=pk)
    
    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=timetable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timetable entry updated successfully!')
            return redirect('manage_timetable')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TimetableForm(instance=timetable)
    
    context = {
        'form': form,
        'title': 'Edit Timetable Entry',
        'timetable': timetable
    }
    return render(request, 'academic/timetable_form.html', context)

@admin_required
def delete_timetable_entry(request, pk):
    """Delete timetable entry"""
    timetable = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        class_name = timetable.class_level.name
        timetable.delete()
        messages.success(request, f'Timetable entry for {class_name} deleted successfully!')
        return redirect('manage_timetable')
    
    context = {
        'timetable': timetable
    }
    return render(request, 'academic/delete_timetable.html', context)

# AJAX views for dynamic filtering
def load_sections(request):
    """Load sections based on selected class"""
    class_id = request.GET.get('class_id')
    sections = Section.objects.filter(class_name_id=class_id).order_by('name')
    return render(request, 'academic/section_dropdown.html', {'sections': sections})

def load_teachers(request):
    """Load teachers based on selected subject"""
    subject_id = request.GET.get('subject_id')
    
    print(f"Loading teachers for subject ID: {subject_id}")  # Debug print
    
    if not subject_id:
        return render(request, 'academic/teacher_dropdown.html', {'teachers': Teacher.objects.none()})
    
    try:
        # Get teachers who teach this subject
        teachers = Teacher.objects.filter(subjects__id=subject_id).distinct()
        print(f"Found {teachers.count()} teachers for subject {subject_id}")  # Debug print
        
        return render(request, 'academic/teacher_dropdown.html', {'teachers': teachers})
    
    except Exception as e:
        print(f"Error loading teachers: {str(e)}")  # Debug print
        return render(request, 'academic/teacher_dropdown.html', {'teachers': Teacher.objects.none()})

def is_current_period(start_time, end_time):
    """Check if current time falls within this period"""
    from datetime import datetime
    now = datetime.now().time()
    return start_time <= now <= end_time

def create_sample_periods_structure():
    """Create sample period structure when no timetable exists"""
    sample_periods = [
        {'start': time(8, 0), 'end': time(8, 40)},
        {'start': time(8, 40), 'end': time(9, 20)},
        {'start': time(9, 20), 'end': time(10, 0)},
        {'start': time(10, 0), 'end': time(10, 20), 'is_break': True, 'break_name': 'Short Break'},
        {'start': time(10, 20), 'end': time(11, 0)},
        {'start': time(11, 0), 'end': time(11, 40)},
        {'start': time(11, 40), 'end': time(12, 20)},
        {'start': time(12, 20), 'end': time(13, 0), 'is_break': True, 'break_name': 'Lunch Break'},
        {'start': time(13, 0), 'end': time(13, 40)},
        {'start': time(13, 40), 'end': time(14, 20)},
    ]
    
    periods_data = []
    for i, period in enumerate(sample_periods, 1):
        period_data = {
            'id': i,
            'period_number': i,
            'start_time': period['start'],
            'end_time': period['end'],
            'is_break': period.get('is_break', False),
            'break_name': period.get('break_name', ''),
            'is_current': is_current_period(period['start'], period['end']),
        }
        
        # Initialize empty data for all days
        for day_code, day_name in Timetable.DAY_CHOICES:
            period_data[f'{day_code.lower()}_subject'] = None
            period_data[f'{day_code.lower()}_teacher'] = None
            period_data[f'{day_code.lower()}_room'] = ''
        
        periods_data.append(period_data)
    
    return periods_data

@admin_required
def generate_timetable(request):
    """Generate timetable automatically"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        clear_existing = request.POST.get('clear_existing')
        
        try:
            class_obj = Class.objects.get(id=class_id)
            
            if clear_existing:
                # Clear existing timetable for this class
                Timetable.objects.filter(class_level=class_obj).delete()
            
            # Simple timetable generation logic
            # This is a basic implementation - you can enhance it with more sophisticated algorithms
            sections = Section.objects.filter(class_name=class_obj)
            subjects = Subject.objects.all()
            teachers = Teacher.objects.all()
            
            periods_per_day = 8
            days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
            
            created_count = 0
            for section in sections:
                for day in days:
                    for period in range(1, periods_per_day + 1):
                        # Skip periods that are breaks
                        if period == 4:  # Short break
                            Timetable.objects.create(
                                class_level=class_obj,
                                section=section,
                                day=day,
                                period_number=period,
                                start_time=time(10, 0),
                                end_time=time(10, 20),
                                is_break=True,
                                break_name='Short Break'
                            )
                            created_count += 1
                            continue
                        elif period == 7:  # Lunch break
                            Timetable.objects.create(
                                class_level=class_obj,
                                section=section,
                                day=day,
                                period_number=period,
                                start_time=time(12, 20),
                                end_time=time(13, 0),
                                is_break=True,
                                break_name='Lunch Break'
                            )
                            created_count += 1
                            continue
                        
                        # Assign subject and teacher (basic assignment)
                        subject_index = (period - 1) % subjects.count()
                        teacher_index = (period - 1) % teachers.count()
                        
                        subject = subjects[subject_index]
                        teacher = teachers[teacher_index]
                        
                        # Calculate times
                        start_hour = 8 + (period - 1) * 1
                        if period > 4:  # After short break
                            start_hour += 1  # Account for break time
                        if period > 7:  # After lunch break
                            start_hour += 1  # Account for lunch time
                        
                        Timetable.objects.create(
                            class_level=class_obj,
                            section=section,
                            subject=subject,
                            teacher=teacher,
                            day=day,
                            period_number=period,
                            start_time=time(start_hour, 0),
                            end_time=time(start_hour, 40),
                            room=f"Room {period}"
                        )
                        created_count += 1
            
            messages.success(request, f'Timetable generated successfully! Created {created_count} entries for {class_obj.name}.')
            return redirect('manage_timetable')
            
        except Exception as e:
            messages.error(request, f'Error generating timetable: {str(e)}')
    
    classes = Class.objects.all()
    academic_years = AcademicYear.objects.all()
    context = {
        'classes': classes,
        'academic_years': academic_years,
    }
    return render(request, 'academic/generate_timetable.html', context)

@login_required
def class_timetable(request, class_id):
    """View timetable for a specific class"""
    class_obj = get_object_or_404(Class, id=class_id)
    
    timetable_entries = Timetable.objects.filter(
        class_level=class_obj
    ).select_related('subject', 'teacher', 'section').order_by('day', 'period_number')
    
    # Organize by day and period
    timetable_data = {}
    for entry in timetable_entries:
        day = entry.get_day_display()
        if day not in timetable_data:
            timetable_data[day] = {}
        timetable_data[day][entry.period_number] = entry
    
    context = {
        'class_obj': class_obj,
        'timetable_data': timetable_data,
        'periods_range': range(1, 9),  # 8 periods per day
    }
    return render(request, 'academic/class_timetable.html', context)

# AJAX API endpoints
@admin_required
def save_period_ajax(request):
    """Save period via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            print("Received AJAX data:", data)  # Debug print
            
            # Validate required fields
            required_fields = ['class_level', 'section', 'day', 'period_number', 'start_time', 'end_time']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({'success': False, 'error': f'Missing required field: {field}'})
            
            # Convert time strings to time objects
            try:
                start_time = datetime.strptime(data['start_time'], '%H:%M').time()
                end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            except ValueError as e:
                return JsonResponse({'success': False, 'error': f'Invalid time format: {str(e)}'})
            
            # Check if it's a break period
            is_break = data.get('is_break', False)
            break_name = data.get('break_name', '')
            
            # For break periods, clear subject and teacher
            subject_id = None if is_break else data.get('subject')
            teacher_id = None if is_break else data.get('teacher')
            
            # Validate subject and teacher for non-break periods
            if not is_break:
                if not subject_id:
                    return JsonResponse({'success': False, 'error': 'Subject is required for non-break periods'})
                if not teacher_id:
                    return JsonResponse({'success': False, 'error': 'Teacher is required for non-break periods'})
            
            # Check for conflicts
            conflict_check = Timetable.objects.filter(
                class_level_id=data['class_level'],
                section_id=data['section'],
                day=data['day'],
                period_number=data['period_number']
            )
            
            # If we're updating an existing entry, exclude it from conflict check
            entry_id = data.get('entry_id')
            if entry_id:
                conflict_check = conflict_check.exclude(pk=entry_id)
            
            if conflict_check.exists():
                return JsonResponse({
                    'success': False, 
                    'error': 'A timetable entry already exists for this class, section, day, and period.'
                })
            
            # Check for teacher conflicts (only for non-break periods)
            if teacher_id and not is_break:
                teacher_conflict = Timetable.objects.filter(
                    teacher_id=teacher_id,
                    day=data['day'],
                    period_number=data['period_number']
                )
                
                if entry_id:
                    teacher_conflict = teacher_conflict.exclude(pk=entry_id)
                
                if teacher_conflict.exists():
                    conflict_entry = teacher_conflict.first()
                    return JsonResponse({
                        'success': False,
                        'error': f'Teacher is already assigned to {conflict_entry.class_level.name} during this period.'
                    })
            
            # Create or update timetable entry
            if entry_id:
                # Update existing entry
                try:
                    timetable = Timetable.objects.get(pk=entry_id)
                    timetable.class_level_id = data['class_level']
                    timetable.section_id = data['section']
                    timetable.subject_id = subject_id
                    timetable.teacher_id = teacher_id
                    timetable.day = data['day']
                    timetable.period_number = data['period_number']
                    timetable.start_time = start_time
                    timetable.end_time = end_time
                    timetable.room = data.get('room', '')
                    timetable.is_break = is_break
                    timetable.break_name = break_name
                    timetable.save()
                    
                    action = 'updated'
                    
                except Timetable.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Timetable entry not found'})
            else:
                # Create new entry
                timetable = Timetable.objects.create(
                    class_level_id=data['class_level'],
                    section_id=data['section'],
                    subject_id=subject_id,
                    teacher_id=teacher_id,
                    day=data['day'],
                    period_number=data['period_number'],
                    start_time=start_time,
                    end_time=end_time,
                    room=data.get('room', ''),
                    is_break=is_break,
                    break_name=break_name
                )
                action = 'created'
            
            # Prepare response data
            response_data = {
                'success': True,
                'message': f'Timetable entry {action} successfully!',
                'entry_id': timetable.id,
                'action': action
            }
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'Invalid JSON data: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method or not AJAX'})

@admin_required
def check_period_conflict(request):
    """Check if a period already exists for the given parameters"""
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    day = request.GET.get('day')
    period_number = request.GET.get('period_number')
    exclude_entry = request.GET.get('exclude_entry')
    
    timetable_entries = Timetable.objects.filter(
        class_level_id=class_id,
        section_id=section_id,
        day=day,
        period_number=period_number
    )
    
    if exclude_entry:
        timetable_entries = timetable_entries.exclude(pk=exclude_entry)
    
    exists = timetable_entries.exists()
    
    return JsonResponse({
        'exists': exists,
        'conflict_count': timetable_entries.count()
    })

@login_required
def get_timetable_data(request):
    """Get timetable data via AJAX for filtering"""
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    teacher_id = request.GET.get('teacher_id')
    day = request.GET.get('day')
    include_all = request.GET.get('include_all')
    
    # If include_all is set, get all timetable data for workload calculation
    if include_all:
        timetable_entries = Timetable.objects.select_related(
            'class_level', 'section', 'subject', 'teacher'
        ).all()
    else:
        timetable_entries = Timetable.objects.select_related(
            'class_level', 'section', 'subject', 'teacher'
        ).all()
        
        if class_id:
            timetable_entries = timetable_entries.filter(class_level_id=class_id)
        if section_id:
            timetable_entries = timetable_entries.filter(section_id=section_id)
        if teacher_id:
            timetable_entries = timetable_entries.filter(teacher_id=teacher_id)
        if day:
            timetable_entries = timetable_entries.filter(day=day)
    
    # Format data for response with proper structure
    data = []
    for entry in timetable_entries:
        entry_data = {
            'id': entry.id,
            'class_level': {
                'id': entry.class_level.id,
                'name': entry.class_level.name
            },
            'section': {
                'id': entry.section.id,
                'name': entry.section.name
            },
            'day': entry.day,
            'day_display': entry.get_day_display(),
            'period_number': entry.period_number,
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'room': entry.room,
            'is_break': entry.is_break,
            'break_name': entry.break_name,
        }
        
        # Add subject information
        if entry.subject:
            entry_data['subject'] = {
                'id': entry.subject.id,
                'name': entry.subject.name,
                'code': entry.subject.code
            }
        else:
            entry_data['subject'] = None
            
        # Add teacher information
        if entry.teacher:
            entry_data['teacher'] = {
                'id': entry.teacher.id,
                'name': entry.teacher.full_name,
                'teacher_id': entry.teacher.teacher_id
            }
        else:
            entry_data['teacher'] = None
        
        data.append(entry_data)
    
    return JsonResponse({'data': data})

@login_required
def all_books(request):
    """View all books in the library"""
    books = Book.objects.all().order_by('title')
    
    search_query = request.GET.get('search')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    context = {
        'books': books,
        'search_query': search_query or '',
    }
    return render(request, 'library/all_books.html', context)

@admin_required
def add_book(request):
    """Add a new book to the library"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('all_books')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm()
    
    context = {
        'form': form,
        'title': 'Add New Book'
    }
    return render(request, 'library/book_form.html', context)

@login_required
def book_detail(request, book_id):
    """View book details"""
    book = get_object_or_404(Book, id=book_id)
    
    context = {
        'book': book,
    }
    return render(request, 'library/book_detail.html', context)

@admin_required
def edit_book(request, book_id):
    """Edit book information"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', book_id=book.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm(instance=book)
    
    context = {
        'form': form,
        'title': 'Edit Book',
        'book': book
    }
    return render(request, 'library/book_form.html', context)

@admin_required
def delete_book(request, book_id):
    """Delete a book"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        book_title = book.title
        book.delete()
        messages.success(request, f'Book "{book_title}" deleted successfully!')
        return redirect('all_books')
    
    context = {
        'book': book
    }
    return render(request, 'library/confirm_delete_book.html', context)

@admin_required
def borrow_book(request):
    """Borrow a book"""
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        student_id = request.POST.get('student_id')
        due_date = request.POST.get('due_date')
        
        try:
            book = get_object_or_404(Book, id=book_id)
            student = get_object_or_404(Student, id=student_id)
            
            if not student.user:
                messages.error(request, f'Student {student.get_full_name()} does not have a user account. Cannot borrow book.')
                return redirect('borrow_book')

            if book.available_copies > 0:
                # Convert string due_date to aware datetime at end of day
                due_datetime = timezone.make_aware(datetime.strptime(due_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
                
                # Create borrowing record
                borrowing = BookBorrowing.objects.create(
                    book=book,
                    borrower=student.user,
                    borrowed_date=timezone.now(),
                    due_date=due_datetime,
                    status='BORROWED'
                )
                
                # Update available copies
                book.available_copies -= 1
                book.save()
                
                messages.success(request, f'Book "{book.title}" borrowed successfully!')
            else:
                messages.error(request, 'No copies available for borrowing.')
                
        except Exception as e:
            messages.error(request, f'Error borrowing book: {str(e)}')
    
    books = Book.objects.filter(available_copies__gt=0)
    students = Student.objects.filter(is_active=True, user__isnull=False)
    
    context = {
        'books': books,
        'students': students,
        'today': timezone.now().date(),
    }
    return render(request, 'library/borrow_book.html', context)

@admin_required
def borrowed_books(request):
    """View list of all active borrowings"""
    search_query = request.GET.get('search', '')
    borrowings = BookBorrowing.objects.filter(status='BORROWED').select_related('book', 'borrower')
    
    if search_query:
        borrowings = borrowings.filter(
            Q(book__title__icontains=search_query) |
            Q(borrower__first_name__icontains=search_query) |
            Q(borrower__last_name__icontains=search_query) |
            Q(borrower__username__icontains=search_query)
        )
        
    context = {
        'borrowings': borrowings,
        'search_query': search_query,
    }
    return render(request, 'library/borrowed_list.html', context)

@admin_required
def return_book(request, borrow_id):
    """Return a borrowed book"""
    borrowing = get_object_or_404(BookBorrowing, id=borrow_id)
    
    if request.method == 'POST':
        try:
            # Update borrowing record
            borrowing.returned_date = timezone.now()
            borrowing.status = 'RETURNED'
            borrowing.calculate_fine()
            
            # Update available copies
            book = borrowing.book
            book.available_copies += 1
            book.save()
            
            messages.success(request, f'Book "{book.title}" returned successfully!')
            return redirect('book_detail', book_id=book.id)
            
        except Exception as e:
            messages.error(request, f'Error returning book: {str(e)}')
    
    return redirect('all_books')

@login_required
@admin_required
def exam_schedule(request):
    """Display exam schedule"""
    exams = Exam.objects.all().select_related('subject', 'class_level', 'created_by')
    classes = Class.objects.all()
    subjects = Subject.objects.all()
    
    # Statistics
    total_exams = exams.count()
    upcoming_exams = exams.filter(status='UPCOMING').count()
    ongoing_exams = exams.filter(status='ONGOING').count()
    completed_exams = exams.filter(status='COMPLETED').count()
    
    context = {
        'exams': exams,
        'classes': classes,
        'subjects': subjects,
        'total_exams': total_exams,
        'upcoming_exams': upcoming_exams,
        'ongoing_exams': ongoing_exams,
        'completed_exams': completed_exams,
        'title': 'Exam Schedule'
    }
    return render(request, 'examinations/exam_schedule.html', context)

@admin_required
def create_exam_schedule(request):
    """Create exam schedule"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(created_by=request.user)
            messages.success(request, f'Exam "{exam.name}" scheduled successfully!')
            return redirect('exam_schedule')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamForm()
    
    context = {
        'form': form,
        'title': 'Schedule New Exam'
    }
    return render(request, 'examinations/exam_schedule_form.html', context)

@admin_required
def exam_grades(request):
    """View and manage exam grading system"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    grading_system = GradingSystem.objects.all().order_by('-min_mark')
    
    if request.method == 'POST':
        form = GradingSystemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grading scale added successfully!')
            return redirect('exam_grades')
        else:
            messages.error(request, 'Error adding grading scale. Please check the values.')
    else:
        form = GradingSystemForm()
    
    context = {
        'grading_system': grading_system,
        'form': form,
        'title': 'Grading System Management'
    }
    return render(request, 'examinations/exam_grades.html', context)

@admin_required
def delete_grading_system(request, grade_id):
    """Delete a grading scale"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('login')
    
    grade = get_object_or_404(GradingSystem, id=grade_id)
    if request.method == 'POST':
        grade_name = grade.grade
        grade.delete()
        messages.success(request, f'Grade {grade_name} deleted successfully!')
    
    return redirect('exam_grades')

@admin_required
def edit_grading_system(request, grade_id):
    """Edit a grading scale"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    grade = get_object_or_404(GradingSystem, id=grade_id)
    
    if request.method == 'POST':
        form = GradingSystemForm(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grading scale updated successfully!')
            return redirect('exam_grades')
    else:
        form = GradingSystemForm(instance=grade)
    
    context = {
        'form': form,
        'grade': grade,
        'title': 'Edit Grading Scale'
    }
    return render(request, 'examinations/edit_grading.html', context)

@admin_required
def setup_grading_system(request):
    """Setup initial grading system with standard CBC defaults"""
    # Clear existing to ensure "only" CBC standards are used
    GradingSystem.objects.all().delete()
    
    default_grades = [
        {'name': 'Exceeding Expectations', 'min_mark': 80, 'max_mark': 100, 'grade': 'EE', 'points': 4.0, 'remarks': 'Exceeding Expectations'},
        {'name': 'Meeting Expectations', 'min_mark': 50, 'max_mark': 79.99, 'grade': 'ME', 'points': 3.0, 'remarks': 'Meeting Expectations'},
        {'name': 'Approaching Expectations', 'min_mark': 40, 'max_mark': 49.99, 'grade': 'AE', 'points': 2.0, 'remarks': 'Approaching Expectations'},
        {'name': 'Below Expectations', 'min_mark': 0, 'max_mark': 39.99, 'grade': 'BE', 'points': 1.0, 'remarks': 'Below Expectations'},
    ]
    
    for g in default_grades:
        GradingSystem.objects.create(**g)
    
    messages.success(request, 'CBC performance standards initialized successfully!')
    return redirect('exam_grades')

@login_required
def add_exam(request):
    """Add a new exam"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, f'Exam "{exam.name}" created successfully!')
            return redirect('exam_schedule')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamForm()
    
    context = {
        'form': form,
        'title': 'Schedule New Exam'
    }
    return render(request, 'examinations/add_exam.html', context)



@admin_required
def transport_management(request):
    """Transport management dashboard"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    # Transport statistics
    total_vehicles = Vehicle.objects.count()
    total_routes = TransportRoute.objects.count()
    assigned_students = Student.objects.filter(transport_route__isnull=False).count()
    
    vehicles = Vehicle.objects.all().select_related('route')
    
    context = {
        'total_vehicles': total_vehicles,
        'total_routes': total_routes,
        'assigned_students': assigned_students,
        'vehicles': vehicles,
    }
    return render(request, 'transport/transport_management.html', context)

@admin_required
def transport_routes(request):
    """View transport routes"""
    routes = TransportRoute.objects.all()
    
    context = {
        'routes': routes,
    }
    return render(request, 'transport/transport_routes.html', context)

@admin_required
def transport_vehicles(request):
    """View transport vehicles"""
    vehicles = Vehicle.objects.all().select_related('route')
    
    context = {
        'vehicles': vehicles,
    }
    return render(request, 'transport/transport_vehicles.html', context)

@admin_required
def assign_transport(request):
    """Assign transport to students"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        route_id = request.POST.get('route_id')
        
        try:
            student = get_object_or_404(Student, id=student_id)
            route = get_object_or_404(TransportRoute, id=route_id)
            student.transport_route = route
            student.save()
            
            messages.success(request, f'Transport assigned to {student.full_name} successfully!')
            
        except Exception as e:
            messages.error(request, f'Error assigning transport: {str(e)}')
    
    students = Student.objects.filter(is_active=True).select_related('current_class', 'current_section', 'transport_route')
    routes = TransportRoute.objects.all()
    
    context = {
        'students': students,
        'routes': routes,
    }
    return render(request, 'transport/assign_transport.html', context)

@admin_required
def remove_transport_assignment(request, student_id):
    """Remove transport assignment from a student"""
    student = get_object_or_404(Student, id=student_id)
    student.transport_route = None
    student.save()
    messages.success(request, f'Transport assignment removed for {student.full_name}.')
    return redirect('assign_transport')

@admin_required
def add_route(request):
    """Add a new transport route"""
    if request.method == 'POST':
        form = TransportRouteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New route added successfully!')
            return redirect('transport_routes')
    else:
        form = TransportRouteForm()
    
    return render(request, 'transport/route_form.html', {'form': form, 'title': 'Add New Route'})

@admin_required
def edit_route(request, pk):
    """Edit an existing transport route"""
    route = get_object_or_404(TransportRoute, pk=pk)
    if request.method == 'POST':
        form = TransportRouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, 'Route updated successfully!')
            return redirect('transport_routes')
    else:
        form = TransportRouteForm(instance=route)
    
    return render(request, 'transport/route_form.html', {'form': form, 'title': 'Edit Route'})

@admin_required
def delete_route(request, pk):
    """Delete a transport route"""
    route = get_object_or_404(TransportRoute, pk=pk)
    if request.method == 'POST':
        route.delete()
        messages.success(request, 'Route deleted successfully!')
        return redirect('transport_routes')
    return render(request, 'transport/confirm_delete.html', {'item': route, 'type': 'Route'})

@admin_required
def add_vehicle(request):
    """Add a new vehicle"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New vehicle added successfully!')
            return redirect('transport_vehicles')
    else:
        form = VehicleForm()
    
    return render(request, 'transport/vehicle_form.html', {'form': form, 'title': 'Add New Vehicle'})

@admin_required
def edit_vehicle(request, pk):
    """Edit an existing vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehicle updated successfully!')
            return redirect('transport_vehicles')
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'transport/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle'})

@admin_required
def delete_vehicle(request, pk):
    """Delete a vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted successfully!')
        return redirect('transport_vehicles')
    return render(request, 'transport/confirm_delete.html', {'item': vehicle, 'type': 'Vehicle'})

@admin_required
def auto_assign_transport(request):
    """Automatically assign routes to students based on address keywords"""
    students_without_route = Student.objects.filter(is_active=True, transport_route__isnull=True)
    routes = TransportRoute.objects.filter(is_active=True)
    
    assigned_count = 0
    for student in students_without_route:
        if student.address:
            addr = student.address.lower()
            for route in routes:
                if (route.name.lower() in addr or 
                    route.start_point.lower() in addr or 
                    route.end_point.lower() in addr):
                    student.transport_route = route
                    student.save()
                    assigned_count += 1
                    break
    
    messages.success(request, f'Smart scan complete. {assigned_count} students auto-assigned to routes.')
    return redirect('assign_transport')

@admin_required
def generate_standard_routes(request):
    """Generate a set of standard school routes for Nairobi/Local area"""
    standard_routes = [
        {"name": "Sirisia Center Line", "start": "Sirisia Market", "end": "School", "dist": 5.0, "fare": 1500},
        {"name": "Bungoma Town Express", "start": "Bungoma CBD", "end": "School", "dist": 12.5, "fare": 3000},
        {"name": "Chwele Road Route", "start": "Chwele", "end": "School", "dist": 18.2, "fare": 4000},
        {"name": "Malakisi Service", "start": "Malakisi", "end": "School", "dist": 22.0, "fare": 4500},
        {"name": "Kanduyi Loop", "start": "Kanduyi", "end": "School", "dist": 10.5, "fare": 2500},
        {"name": "Kimilili Link", "start": "Kimilili", "end": "School", "dist": 28.5, "fare": 5500},
        {"name": "Lwakhakha Border Line", "start": "Lwakhakha", "end": "School", "dist": 35.0, "fare": 6500},
        {"name": "Namwela Route", "start": "Namwela", "end": "School", "dist": 15.8, "fare": 3500},
        {"name": "Butula Connection", "start": "Butula", "end": "School", "dist": 40.0, "fare": 7500},
        {"name": "Webuye Interchange", "start": "Webuye", "end": "School", "dist": 45.0, "fare": 8000},
    ]
    
    created_count = 0
    for r in standard_routes:
        route, created = TransportRoute.objects.get_or_create(
            name=r["name"],
            defaults={
                "start_point": r["start"],
                "end_point": r["end"],
                "distance": r["dist"],
                "fare": r["fare"],
                "description": f"Standard school transport service for {r['name']} area."
            }
        )
        if created:
            created_count += 1
            
    if created_count > 0:
        messages.success(request, f"Successfully generated {created_count} standard transport routes.")
    else:
        messages.info(request, "Standard routes already exist or no new routes were added.")
        
    return redirect('transport_routes')

@admin_required
def hostel_management(request):
    """Hostel management dashboard"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    # Hostel statistics
    hostels_count = Hostel.objects.count()
    total_rooms = HostelRoom.objects.count()
    total_capacity = HostelRoom.objects.aggregate(Sum('capacity'))['capacity__sum'] or 0
    occupied_beds = HostelAllocation.objects.filter(status='ACTIVE').count()
    available_beds = total_capacity - occupied_beds
    
    # Recent allocations
    recent_allocations = HostelAllocation.objects.all().select_related('student', 'room', 'room__hostel').order_by('-allocated_date')[:5]
    
    # Hostels by type
    boys_hostels = Hostel.objects.filter(type='BOYS').count()
    girls_hostels = Hostel.objects.filter(type='GIRLS').count()

    context = {
        'hostels_count': hostels_count,
        'total_rooms': total_rooms,
        'total_capacity': total_capacity,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'recent_allocations': recent_allocations,
        'boys_hostels': boys_hostels,
        'girls_hostels': girls_hostels,
    }
    return render(request, 'hostel/hostel_management.html', context)

@admin_required
def hostel_list(request):
    """List all hostels"""
    hostels = Hostel.objects.all()
    context = {
        'hostels': hostels,
    }
    return render(request, 'hostel/hostel_list.html', context)

@admin_required
def add_hostel(request):
    """Add new hostel"""
    if request.method == 'POST':
        form = HostelForm(request.POST)
        if form.is_valid():
            hostel = form.save()
            messages.success(request, f'Hostel {hostel.name} created successfully!')
            return redirect('hostel_list')
    else:
        form = HostelForm()
    
    context = {
        'form': form,
        'title': 'Add New Hostel',
    }
    return render(request, 'hostel/hostel_form.html', context)

@admin_required
def edit_hostel(request, pk):
    """Edit hostel details"""
    hostel = get_object_or_404(Hostel, pk=pk)
    if request.method == 'POST':
        form = HostelForm(request.POST, instance=hostel)
        if form.is_valid():
            hostel = form.save()
            messages.success(request, f'Hostel {hostel.name} updated successfully!')
            return redirect('hostel_list')
    else:
        form = HostelForm(instance=hostel)
    
    context = {
        'form': form,
        'title': f'Edit Hostel: {hostel.name}',
    }
    return render(request, 'hostel/hostel_form.html', context)

@admin_required
def delete_hostel(request, pk):
    """Delete hostel"""
    hostel = get_object_or_404(Hostel, pk=pk)
    if request.method == 'POST':
        name = hostel.name
        hostel.delete()
        messages.success(request, f'Hostel {name} deleted successfully!')
        return redirect('hostel_list')
    return render(request, 'hostel/hostel_confirm_delete.html', {'hostel': hostel})

@admin_required
def hostel_rooms(request):
    """View hostel rooms"""
    hostel_id = request.GET.get('hostel')
    status_filter = request.GET.get('status')
    
    rooms = HostelRoom.objects.all().select_related('hostel')
    
    if hostel_id:
        rooms = rooms.filter(hostel_id=hostel_id)
    if status_filter:
        rooms = rooms.filter(status=status_filter)
        
    hostels = Hostel.objects.all()
    
    context = {
        'rooms': rooms,
        'hostels': hostels,
    }
    return render(request, 'hostel/hostel_rooms.html', context)

@admin_required
def add_hostel_room(request):
    """Add new room to a hostel"""
    if request.method == 'POST':
        form = HostelRoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            # Update hostel counts
            hostel = room.hostel
            hostel.total_rooms = hostel.rooms.count()
            # We should recalculate available rooms if needed, but the model has it as integer
            # Let's just keep it simple for now
            hostel.save()
            
            messages.success(request, f'Room {room.room_number} added successfully!')
            return redirect('hostel_rooms')
    else:
        form = HostelRoomForm()
    
    context = {
        'form': form,
        'title': 'Add New Room',
    }
    return render(request, 'hostel/room_form.html', context)

@admin_required
def edit_hostel_room(request, pk):
    """Edit room details"""
    room = get_object_or_404(HostelRoom, pk=pk)
    if request.method == 'POST':
        form = HostelRoomForm(request.POST, instance=room)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Room {room.room_number} updated successfully!')
            return redirect('hostel_rooms')
    else:
        form = HostelRoomForm(instance=room)
    
    context = {
        'form': form,
        'title': f'Edit Room: {room.room_number}',
    }
    return render(request, 'hostel/room_form.html', context)

@admin_required
def delete_hostel_room(request, pk):
    """Delete room"""
    room = get_object_or_404(HostelRoom, pk=pk)
    if request.method == 'POST':
        num = room.room_number
        hostel = room.hostel
        room.delete()
        # Update hostel counts
        hostel.total_rooms = hostel.rooms.count()
        hostel.save()
        messages.success(request, f'Room {num} deleted successfully!')
        return redirect('hostel_rooms')
    return render(request, 'hostel/room_confirm_delete.html', {'room': room})

@admin_required
def hostel_allocations(request):
    """View hostel allocations"""
    allocations = HostelAllocation.objects.all().select_related('student', 'room', 'room__hostel').order_by('-allocated_date')
    
    context = {
        'allocations': allocations,
    }
    return render(request, 'hostel/hostel_allocations.html', context)

@admin_required
def allocate_hostel(request):
    """Allocate hostel to students"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        form = HostelAllocationForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            room = form.cleaned_data['room']
            
            # Check if student already has an active allocation
            if HostelAllocation.objects.filter(student=student, status='ACTIVE').exists():
                messages.error(request, f'{student.get_full_name()} already has an active hostel allocation.')
            elif room.available_beds <= 0:
                messages.error(request, f'No available beds in Room {room.room_number}.')
            else:
                allocation = form.save()
                room.refresh_from_db()
                # Update room status if full
                if room.available_beds <= 0:
                    room.status = 'OCCUPIED'
                    room.save()
                
                messages.success(request, f'Hostel allocated to {student.get_full_name()} successfully!')
                return redirect('hostel_allocations')
    else:
        form = HostelAllocationForm()
        # Only show rooms with available beds
        # available_rooms = [r.id for r in HostelRoom.objects.all() if r.available_beds > 0]
        # form.fields['room'].queryset = HostelRoom.objects.filter(id__in=available_rooms, status='AVAILABLE')
    
    context = {
        'form': form,
        'title': 'New Hostel Allocation',
        'students': Student.objects.filter(is_active=True),
        'rooms': HostelRoom.objects.filter(status='AVAILABLE'),
    }
    return render(request, 'hostel/allocate_hostel.html', context)

@admin_required
def cancel_hostel_allocation(request, pk):
    """Cancel or complete an allocation"""
    allocation = get_object_or_404(HostelAllocation, pk=pk)
    if request.method == 'POST':
        allocation.status = 'COMPLETED'
        allocation.completion_date = timezone.now().date()
        allocation.save()
        
        # Check if room can be set back to available
        room = allocation.room
        if room.status == 'OCCUPIED' and room.available_beds > 0:
            room.status = 'AVAILABLE'
            room.save()
            
        messages.success(request, f'Allocation for {allocation.student.get_full_name()} completed.')
        return redirect('hostel_allocations')
    return redirect('hostel_allocations')

@login_required
def alerts(request):
    """UI Elements - Alerts"""
    return render(request, 'ui_elements/alerts.html')

@login_required
def grid(request):
    """UI Elements - Grid"""
    return render(request, 'ui_elements/grid.html')

@login_required
def progress_bars(request):
    """UI Elements - Progress Bars"""
    return render(request, 'ui_elements/progress_bars.html')

@admin_required
def update_parent(request, parent_id):
    """Update parent information"""
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        try:
            # Update parent user
            parent.user.first_name = request.POST.get('first_name', parent.first_name)
            parent.user.last_name = request.POST.get('last_name', parent.last_name)
            parent.user.email = request.POST.get('email', parent.email)
            parent.user.save()
            
            # Update parent profile
            parent.first_name = request.POST.get('first_name', parent.first_name)
            parent.last_name = request.POST.get('last_name', parent.last_name)
            parent.phone = request.POST.get('phone', parent.phone)
            parent.email = request.POST.get('email', parent.email)
            parent.address = request.POST.get('address', parent.address)
            parent.occupation = request.POST.get('occupation', parent.occupation)
            parent.father_name = request.POST.get('father_name', parent.father_name)
            parent.mother_name = request.POST.get('mother_name', parent.mother_name)
            
            # Handle photo upload
            print(f"DEBUG: Files received: {request.FILES}")
            if 'photo' in request.FILES:
                parent.photo = request.FILES['photo']
            
            parent.save()
            
            messages.success(request, f'Parent {parent.full_name} updated successfully!')
            return redirect('parent_details', parent_id=parent.id)
            
        except Exception as e:
            messages.error(request, f'Error updating parent: {str(e)}')
    
    context = {
        'parent': parent,
    }
    return render(request, 'parents/update_parent.html', context)

@admin_required
def delete_parent(request, parent_id):
    """Delete a parent"""
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        try:
            parent_name = parent.full_name
            parent_user = parent.user
            
            # Delete parent profile and user
            parent.delete()
            parent_user.delete()
            
            messages.success(request, f'Parent {parent_name} deleted successfully!')
            return redirect('all_parents')
            
        except Exception as e:
            messages.error(request, f'Error deleting parent: {str(e)}')
    
    context = {
        'parent': parent,
    }
    return render(request, 'parents/delete_parent.html', context)

@admin_required
def update_teacher(request, teacher_id):
    """Update teacher information"""
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    
    if request.method == 'POST':
        try:
            # Update teacher user
            teacher.user.first_name = request.POST.get('first_name', teacher.first_name)
            teacher.user.last_name = request.POST.get('last_name', teacher.last_name)
            teacher.user.email = request.POST.get('email', teacher.email)
            teacher.user.save()
            
            # Update teacher profile
            teacher.first_name = request.POST.get('first_name', teacher.first_name)
            teacher.last_name = request.POST.get('last_name', teacher.last_name)
            teacher.gender = request.POST.get('gender', teacher.gender)
            teacher.date_of_birth = request.POST.get('date_of_birth', teacher.date_of_birth)
            teacher.religion = request.POST.get('religion', teacher.religion)
            teacher.phone = request.POST.get('phone', teacher.phone)
            teacher.email = request.POST.get('email', teacher.email)
            teacher.address = request.POST.get('address', teacher.address)
            teacher.qualification = request.POST.get('qualification', teacher.qualification)
            teacher.specialization = request.POST.get('specialization', teacher.specialization)
            
            try:
                experience = request.POST.get('experience')
                teacher.experience = int(experience) if experience and experience.strip() else 0
            except (ValueError, TypeError):
                pass
                
            try:
                salary = request.POST.get('salary')
                if salary and salary.strip():
                    teacher.salary = Decimal(salary)
            except (InvalidOperation, ValueError, TypeError):
                pass
            
            if 'photo' in request.FILES:
                teacher.photo = request.FILES['photo']
            
            teacher.save()
            
            # Update subjects
            subject_ids = request.POST.getlist('subjects')
            teacher.subjects.set(subject_ids)

            class_teacher_id = request.POST.get('class_teacher')
            if class_teacher_id:
                # Check if the class already has a teacher and it's not the current teacher
                target_class = get_object_or_404(Class, id=class_teacher_id)
                if target_class.class_teacher and target_class.class_teacher != teacher:
                    messages.error(request, f'Class {target_class.name} already has {target_class.class_teacher.full_name} as its class teacher.')
                    return redirect('update_teacher', teacher_id=teacher.teacher_id)
                
                # Clear this teacher from any other classes they might be managing
                Class.objects.filter(class_teacher=teacher).update(class_teacher=None)
                # Assign to new class
                target_class.class_teacher = teacher
                target_class.save()
                teacher.class_teacher = target_class
            else:
                # If they cleared the class teacher field
                Class.objects.filter(class_teacher=teacher).update(class_teacher=None)
                teacher.class_teacher = None
            
            assigned_class_ids = request.POST.getlist('assigned_classes')
            teacher.assigned_classes.set(assigned_class_ids)
            teacher.schedule = request.POST.get('schedule', '')

            teacher.save()
            
            messages.success(request, f'Teacher {teacher.full_name} updated successfully!')
            return redirect('teacher_details', teacher_id=teacher.teacher_id)
            
        except Exception as e:
            print(f"Update teacher error: {e}")
            messages.error(request, f'Error updating teacher: {str(e)}')
    
    subjects = Subject.objects.all()
    # Only show classes that don't have a teacher, or the current teacher's class
    available_classes = Class.objects.filter(Q(class_teacher__isnull=True) | Q(class_teacher=teacher))
    all_classes = Class.objects.all()
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'classes': available_classes,
        'all_classes': all_classes,
    }
    return render(request, 'teachers/update_teacher.html', context)

@admin_required
def delete_teacher(request, teacher_id):
    """Delete a teacher"""
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    
    if request.method == 'POST':
        try:
            teacher_name = teacher.full_name
            teacher_user = teacher.user
            
            # Delete teacher profile and user
            teacher.delete()
            teacher_user.delete()
            
            messages.success(request, f'Teacher {teacher_name} deleted successfully!')
            return redirect('all_teachers')
            
        except Exception as e:
            messages.error(request, f'Error deleting teacher: {str(e)}')
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'teachers/delete_teacher.html', context)

@admin_required
def teacher_payment_detail(request, payment_id):
    """View teacher payment details"""
    # payment = get_object_or_404(TeacherPayment, id=payment_id)
    # context = {
    #     'payment': payment,
    # }
    # return render(request, 'teachers/teacher_payment_detail.html', context)
    messages.info(request, 'Teacher payment detail view will be implemented soon.')
    return redirect('teacher_payment')

@admin_required
def add_teacher_payment(request):
    """Add teacher payment"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    if request.method == 'POST':
        try:
            teacher_id = request.POST.get('teacher')
            amount = request.POST.get('amount')
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method')
            remarks = request.POST.get('remarks', '')
            
            teacher = get_object_or_404(Teacher, id=teacher_id)
            
            # Create payment record
            # TeacherPayment.objects.create(
            #     teacher=teacher,
            #     amount=amount,
            #     payment_date=payment_date,
            #     payment_method=payment_method,
            #     remarks=remarks,
            #     processed_by=request.user
            # )
            
            messages.success(request, f'Payment of {amount} processed for {teacher.full_name}!')
            return redirect('teacher_payment')
            
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    teachers = Teacher.objects.filter(is_active=True)
    context = {
        'teachers': teachers,
    }
    return render(request, 'teachers/add_teacher_payment.html', context)

@admin_required
def reject_admission(request, admission_id):
    """Reject an admission application"""
    admission = get_object_or_404(AdmissionForm, id=admission_id)
    
    if admission.status != 'PENDING':
        messages.warning(request, 'This admission has already been processed.')
        return redirect('manage_admissions')
    
    if request.method == 'POST':
        try:
            admission.status = 'REJECTED'
            admission.reviewed_by = request.user
            admission.reviewed_date = timezone.now()
            admission.rejection_reason = request.POST.get('rejection_reason', '')
            admission.save()
            
            messages.success(request, f'Admission for {admission.first_name} {admission.last_name} has been rejected.')
            
        except Exception as e:
            messages.error(request, f'Error rejecting admission: {str(e)}')
    
    return redirect('manage_admissions')

@admin_required
def admission_details(request, admission_id):
    """View admission details"""
    admission = get_object_or_404(AdmissionForm, id=admission_id)
    
    context = {
        'admission': admission,
    }
    return render(request, 'students/admission_details.html', context)

@login_required
def get_students_by_class(request, class_id):
    """AJAX view to get students by class"""
    students = Student.objects.filter(
        current_class_id=class_id,
        is_active=True
    ).order_by('roll_number')
    
    students_data = []
    for student in students:
        students_data.append({
            'id': student.id,
            'name': student.full_name,
            'roll_number': student.roll_number,
            'student_id': student.student_id,
        })
    
    return JsonResponse({
        'success': True,
        'students': students_data
    })

@login_required
def get_subjects_by_class(request, class_id):
    """AJAX view to get subjects by class"""
    # This would typically query a ClassSubject relationship
    # For now, return all subjects
    subjects = Subject.objects.all()
    
    subjects_data = []
    for subject in subjects:
        subjects_data.append({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
        })
    
    return JsonResponse({
        'success': True,
        'subjects': subjects_data
    })

@login_required
def edit_exam(request, exam_id):
    """Edit an existing exam - accessible by both teachers and admin"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check permissions: either the user created the exam OR user is staff/admin
    if not (request.user.is_staff or exam.created_by == request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    
    # For teachers, get their teacher profile
    teacher = getattr(request.user, 'teacher', None)
    
    if request.method == 'POST':
        # Pass teacher only if it exists (for teachers, not for admin)
        form_kwargs = {'instance': exam}
        if teacher:
            form_kwargs['teacher'] = teacher
            
        form = ExamForm(request.POST, **form_kwargs)
        
        if form.is_valid():
            try:
                updated_exam = form.save()
                messages.success(request, f'Exam "{updated_exam.name}" updated successfully!')
                
                # Redirect based on user type
                if request.user.is_staff:
                    return redirect('exam_schedule')  # or wherever admin should go
                else:
                    return redirect('teacher_exam_management')
                    
            except Exception as e:
                messages.error(request, f'Error updating exam: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pass teacher only if it exists (for teachers, not for admin)
        form_kwargs = {'instance': exam}
        if teacher:
            form_kwargs['teacher'] = teacher
            
        form = ExamForm(**form_kwargs)
    
    context = {
        'form': form,
        'exam': exam,
        'title': f'Edit {exam.name}',
        'is_admin': request.user.is_staff
    }
    
    # Use appropriate template based on user type
    template_name = 'examinations/edit_exam.html' if request.user.is_staff else 'teachers/exam_form.html'
    return render(request, template_name, context)

@login_required
def delete_exam(request, exam_id):
    # Check if staff OR if teacher created it
    if request.user.is_staff:
        exam = get_object_or_404(Exam, id=exam_id)
    else:
        exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    if request.method == 'POST':
        exam_name = exam.name
        exam.delete()
        messages.success(request, f'Exam "{exam_name}" deleted successfully!')
        
        if request.user.is_staff:
            return redirect('exam_schedule')
        else:
            return redirect('teacher_exam_management')
    
    context = {
        'exam': exam
    }
    return render(request, 'teachers/confirm_delete_exam.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN USER MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def admin_user_management(request):
    """Admin view: list all users with search/filter and inline actions."""
    search_query = request.GET.get('q', '').strip()
    role_filter  = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    users = User.objects.select_related(
        'student', 'teacher'
    ).prefetch_related('groups').order_by('username')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if role_filter == 'student':
        users = users.filter(student__isnull=False)
    elif role_filter == 'teacher':
        users = users.filter(teacher__isnull=False)
    elif role_filter == 'admin':
        users = users.filter(is_staff=True)
    elif role_filter == 'parent':
        users = users.filter(student__isnull=True, teacher__isnull=True, is_staff=False)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    # Annotate each user with a role label for display
    user_list = []
    for user in users:
        if user.is_superuser:
            role = 'Superuser'
        elif user.is_staff:
            role = 'Admin'
        elif hasattr(user, 'teacher'):
            role = 'Teacher'
        elif hasattr(user, 'student'):
            role = 'Student'
        else:
            role = 'Parent / Other'
        user_list.append({'user': user, 'role': role})

    paginator = Paginator(user_list, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_users': users.count(),
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'active_users': User.objects.filter(is_active=True).count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'student_users': User.objects.filter(student__isnull=False).count(),
        'teacher_users': User.objects.filter(teacher__isnull=False).count(),
    }
    return render(request, 'admin/user_management.html', context)


@admin_required
@require_POST
def admin_change_password(request, user_id):
    """Admin view: set a new password for any user."""
    target_user = get_object_or_404(User, id=user_id)
    new_password  = request.POST.get('new_password', '').strip()
    confirm_password = request.POST.get('confirm_password', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Validation
    if not new_password:
        msg = 'Password cannot be empty.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)
        return redirect('admin_user_management')

    if len(new_password) < 8:
        msg = 'Password must be at least 8 characters long.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)
        return redirect('admin_user_management')

    if new_password != confirm_password:
        msg = 'Passwords do not match.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)
        return redirect('admin_user_management')

    target_user.set_password(new_password)
    target_user.save()

    msg = f"Password for '{target_user.username}' changed successfully."
    if is_ajax:
        return JsonResponse({'success': True, 'message': msg})
    messages.success(request, msg)
    return redirect('admin_user_management')


@admin_required
@require_POST
def admin_toggle_user_status(request, user_id):
    """Admin view: activate or deactivate a user account."""
    target_user = get_object_or_404(User, id=user_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Prevent admin from deactivating themselves
    if target_user == request.user:
        msg = 'You cannot deactivate your own account.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)
        return redirect('admin_user_management')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status = 'activated' if target_user.is_active else 'deactivated'
    msg = f"User '{target_user.username}' has been {status}."
    if is_ajax:
        return JsonResponse({'success': True, 'message': msg, 'is_active': target_user.is_active})
    messages.success(request, msg)
    return redirect('admin_user_management')