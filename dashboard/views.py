# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Count, Sum, Q,  Avg, Max, Min, StdDev
from django.db.models.functions import Coalesce
from django.db.models import FloatField, ExpressionWrapper
from core.models import *
from core.forms import *
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

from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied

from django.core.mail import send_mail
from django.template.loader import render_to_string

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

# Add these to your existing imports section
import csv
import io
from io import BytesIO, StringIO
from decimal import Decimal, InvalidOperation

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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
def complete_setup(request):
    """Mark setup as complete and redirect to dashboard"""
    # Check if all required data exists
    classes_exist = Class.objects.exists()
    sections_exist = Section.objects.exists()
    academic_years_exist = AcademicYear.objects.exists()
    
    if classes_exist and sections_exist and academic_years_exist:
        messages.success(request, 'Initial setup completed successfully! You can now use the system.')
        return redirect('dashboard')
    else:
        messages.error(request, 'Please complete all setup steps before continuing.')
        return redirect('initial_setup')

@login_required
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
@login_required
def student_dashboard(request):
    """Dashboard for students"""
    # Ensure only students can access this
    if not hasattr(request.user, 'student'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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
        
        # Fee status
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        fee_status = Fee.objects.filter(
            student=student,
            academic_year=current_academic_year
        ).aggregate(
            total_due=Sum('amount'),
            total_paid=Sum('amount_paid')
        )
        
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

@login_required
def teacher_dashboard(request):
    """Dashboard for teachers"""
    # Ensure only teachers can access this
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def teacher_my_classes(request):
    """View for teacher to see classes they teach"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
    }
    return render(request, 'teachers/my_classes.html', context)

@login_required
def teacher_class_schedule(request):
    """View for teacher's class schedule"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def teacher_my_students(request):
    """View for teacher to see students in their classes"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def teacher_subjects(request):
    """View for teacher to see subjects they teach"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subjects = teacher.subjects.all()
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
    }
    return render(request, 'teachers/subjects.html', context)

@login_required
def teacher_assignments(request):
    """View for teacher to manage assignments"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def teacher_exam_results(request):
    """View for teacher to manage exam results"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def teacher_assignments(request):
    """View for teacher to manage assignments"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def assignment_create(request):
    """Create a new assignment"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def assignment_detail(request, assignment_id):
    """View assignment details and submissions"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def assignment_edit(request, assignment_id):
    """Edit an existing assignment"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def assignment_delete(request, assignment_id):
    """Delete an assignment"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def assignment_download_submissions(request, assignment_id):
    """Download all submissions for an assignment as zip"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

# Add these views to views.py

@login_required
def teacher_exam_management(request):
    """Main exam management dashboard for teachers"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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
    
    # Upcoming exams
    upcoming_exams = Exam.objects.filter(
        created_by=request.user,
        exam_date__gte=timezone.now().date()
    ).order_by('exam_date')[:5]
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'teacher_subjects': teacher_subjects,
        'total_exams': total_exams,
        'exams_this_month': exams_this_month,
        'recent_exams': recent_exams,
        'upcoming_exams': upcoming_exams,
    }
    return render(request, 'teachers/exam_management.html', context)

@login_required
def create_exam(request):
    """Create a new exam"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
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

@login_required
def edit_marks(request, exam_id):
    """Edit existing marks for an exam"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
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
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
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

@login_required
def subject_results(request, subject_id=None):
    """View results for teacher's subjects"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def class_results(request, class_id=None):
    """View results for teacher's classes"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def generate_report_card(request, student_id, term=None):
    """Generate report card for a student"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def export_results_excel(request, exam_id):
    """Export exam results to Excel with comprehensive error handling"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def export_results_pdf(request, exam_id):
    """Export exam results to PDF"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def bulk_upload_results(request, exam_id):
    """Bulk upload results via CSV"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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
@login_required
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

@login_required
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

@login_required
def parent_dashboard(request):
    """Dashboard for parents - fixed version"""
    try:
        # Check if user has parent profile
        if not hasattr(request.user, 'parent'):
            messages.error(request, "Parent profile not found. Please contact administration.")
            return redirect('dashboard')
        
        parent = request.user.parent
        
        print(f"DEBUG: Parent dashboard loaded for {parent.user.username}")
        print(f"DEBUG: Parent data - Phone: {parent.phone}, Email: {parent.email}")
        print(f"DEBUG: Parent full_name: {parent.full_name}")
        
        # Get children using helper function
        children = get_parent_children(parent)
        print(f"DEBUG: Children found: {children.count()}")
        
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
        today = timezone.now().date()
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
        
        # Get fee status
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        for child in children:
            try:
                child_fees = Fee.objects.filter(
                    student=child,
                    academic_year=current_academic_year
                ).aggregate(
                    total_due=Sum('amount'),
                    total_paid=Sum('amount_paid')
                )
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
        })

# Add these views to views.py

@login_required
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

@login_required
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

@login_required
def parent_fee_history(request, parent_id):
    """View fee history for all children of a parent"""
    parent = get_object_or_404(Parent, id=parent_id)
    children = parent.students.filter(is_active=True)
    
    # Get fees for all children
    fees = Fee.objects.filter(
        student__in=children
    ).select_related('student', 'class_level', 'academic_year').order_by('-created_at')
    
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
        'total_due': total_due,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'search_query': search_query,
        'status_filter': status_filter,
        'child_filter': child_filter,
    }
    return render(request, 'parents/fee_history.html', context)

@login_required
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

@login_required
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

# Update the student_details view to include action context
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


@login_required
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
                
                # Generate parent username
                username = guardian_email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # FIXED: Generate parent password - use provided password or parent's firstname + 1234
                provided_password = request.POST.get('parent_password', '').strip()
                if provided_password:
                    password1 = provided_password
                else:
                    # Use father's name or mother's name for password
                    # Alternative: Extract just first name for parent
                    parent_first_name = father_name.split()[0] if father_name and ' ' in father_name else father_name
                    parent_first_name = parent_first_name or mother_name.split()[0] if mother_name and ' ' in mother_name else mother_name
                    parent_first_name = parent_first_name or "Parent"
                    # Clean the name for password (remove spaces, take first part)
                    clean_name = parent_first_name.split()[0] if ' ' in parent_first_name else parent_first_name
                    password1 = f"{clean_name.lower()}1234"
                
                # FIXED: Create Parent User with proper names
                # Use father's name as parent's first name, student's last name as parent's last name
                parent_first_name = father_name or mother_name or "Parent"
                parent_last_name = last_name  # Use student's last name for parent
                
                parent_user = User.objects.create_user(
                    username=username,
                    email=guardian_email,
                    password=password1,
                    first_name=parent_first_name,
                    last_name=parent_last_name
                )
                
                print(f"DEBUG: Parent user created: {parent_user.username}")
                print(f"DEBUG: Parent user names - First: '{parent_user.first_name}', Last: '{parent_user.last_name}'")
                
                # Add parent to Parent group
                from django.contrib.auth.models import Group
                parent_group, created = Group.objects.get_or_create(name='Parent')
                parent_user.groups.add(parent_group)
                print(f"DEBUG: Parent user added to Parent group")
                
                # FIXED: Create Parent profile with proper names
                try:
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
                    print(f"DEBUG: Parent profile created: {parent_profile}")
                    print(f"DEBUG: Parent profile names - First: '{parent_profile.first_name}', Last: '{parent_profile.last_name}'")
                    print(f"DEBUG: Parent profile details - Phone: {parent_profile.phone}, Email: {parent_profile.email}")
                    
                except Exception as e:
                    print(f"DEBUG: Error creating parent profile: {e}")
                    import traceback
                    print(traceback.format_exc())
                    # If parent profile creation fails, we should not proceed
                    parent_user.delete()
                    messages.error(request, f'Error creating parent profile: {str(e)}')
                    classes = Class.objects.all().order_by('name')
                    sections = Section.objects.all().order_by('name')
                    return render(request, 'students/admit_form.html', {
                        'classes': classes,
                        'sections': sections
                    })
                
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

@login_required
def manage_admissions(request):
    """View to manage pending admissions"""
    admissions = AdmissionForm.objects.all().order_by('-submitted_date')
    
    status_filter = request.GET.get('status')
    if status_filter:
        admissions = admissions.filter(status=status_filter)
    
    context = {
        'admissions': admissions,
    }
    return render(request, 'students/manage_admissions.html', context)

@login_required
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

@login_required
def student_promotion(request):
    if request.method == 'POST':
        try:
            student_ids = request.POST.getlist('students')
            new_class_id = request.POST.get('new_class')
            new_section_id = request.POST.get('new_section')
            academic_year_id = request.POST.get('academic_year')
            
            if not student_ids:
                messages.error(request, 'Please select at least one student to promote.')
                return redirect('student_promotion')
            
            # Get or create academic year
            if academic_year_id:
                academic_year = AcademicYear.objects.get(id=academic_year_id)
            else:
                # Get current academic year
                academic_year = AcademicYear.objects.filter(is_current=True).first()
                if not academic_year:
                    academic_year = AcademicYear.objects.first()
            
            students = Student.objects.filter(id__in=student_ids)
            new_class = Class.objects.get(id=new_class_id)
            new_section = Section.objects.get(id=new_section_id) if new_section_id else None
            
            promoted_count = 0
            promotion_records = []
            
            for student in students:
                # Store old class and section for history
                old_class = student.current_class
                old_section = student.current_section
                
                # Update student
                student.current_class = new_class
                if new_section:
                    student.current_section = new_section
                student.save()
                
                # Create promotion record
                promotion_record = PromotionHistory.objects.create(
                    student=student,
                    from_class=old_class,
                    from_section=old_section,
                    to_class=new_class,
                    to_section=new_section,
                    academic_year=academic_year,
                    promoted_by=request.user
                )
                promotion_records.append(promotion_record)
                
                # Update any existing fees for the student to the new academic year
                Fee.objects.filter(student=student).update(academic_year=academic_year)
                
                promoted_count += 1
            
            messages.success(request, f'Successfully promoted {promoted_count} students to {new_class.name} for academic year {academic_year.name}.')
            return redirect('promotion_history')
            
        except Exception as e:
            messages.error(request, f'Error promoting students: {str(e)}')
            print(f"Promotion error: {traceback.format_exc()}")
    
    students = Student.objects.filter(is_active=True)
    classes = Class.objects.all()
    sections = Section.objects.all()
    academic_years = AcademicYear.objects.all()
    
    # Get recent promotions for the history table
    recent_promotions = PromotionHistory.objects.all().select_related(
        'student', 'from_class', 'to_class', 'academic_year', 'promoted_by'
    ).order_by('-promotion_date')[:10]
    
    # Ensure we have at least one academic year
    if not academic_years.exists():
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            current_year = AcademicYear.objects.first()
        academic_years = AcademicYear.objects.all()
    
    context = {
        'students': students,
        'classes': classes,
        'sections': sections,
        'academic_years': academic_years,
        'recent_promotions': recent_promotions,
    }
    return render(request, 'students/student_promotion.html', context)

@login_required
def promotion_history(request):
    """View promotion history"""
    # Get base queryset
    promotions = PromotionHistory.objects.all().select_related(
        'student', 'from_class', 'to_class', 'academic_year', 'promoted_by'
    ).order_by('-promotion_date')
    
    # Store original count before filtering for statistics
    total_promotions_count = promotions.count()
    
    # Filtering
    class_filter = request.GET.get('class')
    student_filter = request.GET.get('student')
    date_filter = request.GET.get('date')
    
    if class_filter:
        promotions = promotions.filter(to_class_id=class_filter)
    
    if student_filter:
        promotions = promotions.filter(
            Q(student__first_name__icontains=student_filter) |
            Q(student__last_name__icontains=student_filter) |
            Q(student__student_id__icontains=student_filter)
        )
    
    if date_filter:
        promotions = promotions.filter(promotion_date__date=date_filter)
    
    # Calculate statistics - FIXED
    # Get unique students from the filtered queryset
    unique_students_count = promotions.values('student').distinct().count()
    
    # Get unique classes from the filtered queryset
    classes_count = promotions.values('to_class').distinct().count()
    
    # This month promotions from the filtered queryset
    this_month = datetime.now().month
    this_year = datetime.now().year
    this_month_count = promotions.filter(
        promotion_date__month=this_month,
        promotion_date__year=this_year
    ).count()
    
    # Pagination
    paginator = Paginator(promotions, 25)  # Show 25 promotions per page
    page_number = request.GET.get('page')
    promotions_page = paginator.get_page(page_number)
    
    context = {
        'promotions': promotions_page,
        'classes': Class.objects.all(),
        'total_promotions_count': total_promotions_count,  # Total before filtering
        'unique_students_count': unique_students_count,
        'classes_count': classes_count,
        'this_month_count': this_month_count,
        'filtered_count': promotions.count(),  # Count after filtering
    }
    return render(request, 'students/promotion_history.html', context)

@login_required
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
            
            if class_id:
                student.current_class = get_object_or_404(Class, id=class_id)
            if section_id:
                student.current_section = get_object_or_404(Section, id=section_id)
            
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
    
    context = {
        'student': student,
        'classes': classes,
        'sections': sections,
    }
    return render(request, 'students/update_student.html', context)

@login_required
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

@login_required
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

@login_required
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

@login_required
def all_teachers(request):
    teachers = Teacher.objects.all().order_by('first_name', 'last_name')
    
    search_query = request.GET.get('search')
    if search_query:
        teachers = teachers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(teacher_id__icontains=search_query) |
            Q(qualification__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    
    # Calculate statistics
    total_teachers = teachers.count()
    active_teachers = teachers.filter(is_active=True).count()
    male_teachers = teachers.filter(gender='M', is_active=True).count()
    female_teachers = teachers.filter(gender='F', is_active=True).count()
    
    # Pagination
    paginator = Paginator(teachers, 25)  # Show 25 teachers per page
    page_number = request.GET.get('page')
    teachers_page = paginator.get_page(page_number)
    
    context = {
        'teachers': teachers_page,
        'search_query': search_query or '',
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'male_teachers': male_teachers,
        'female_teachers': female_teachers,
    }
    return render(request, 'teachers/all_teachers.html', context)

@login_required
def teacher_details(request, teacher_id):
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    
    # Get classes taught by this teacher
    classes_taught = Class.objects.filter(class_teacher=teacher)
    
    # Get all available classes for assignment
    available_classes = Class.objects.filter(class_teacher__isnull=True)
    
    # Calculate additional statistics
    total_students = Student.objects.filter(current_class__in=classes_taught).count()
    
    context = {
        'teacher': teacher,
        'classes_taught': classes_taught,
        'available_classes': available_classes,
        'total_students': total_students,
    }
    return render(request, 'teachers/teacher_details.html', context)

@login_required
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
            
            messages.success(request, f'Teacher {teacher.full_name} added successfully!')
            return redirect('all_teachers')
            
        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')
    
    # GET request - show form with context
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'today': timezone.now().date(),
    }
    return render(request, 'teachers/add_teacher.html', context)

@login_required
def assign_teacher_classes(request, teacher_id):
    """Assign classes to a teacher"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    
    if request.method == 'POST':
        try:
            class_ids = request.POST.getlist('classes')
            
            # Clear current class assignments for this teacher
            Class.objects.filter(class_teacher=teacher).update(class_teacher=None)
            
            # Assign new classes
            if class_ids:
                classes_to_assign = Class.objects.filter(id__in=class_ids)
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

@login_required
def remove_teacher_class(request, teacher_id, class_id):
    """Remove a specific class from a teacher"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def teacher_payment(request):
    if request.method == 'POST':
        try:
            teacher_id = request.POST.get('teacher')
            amount = request.POST.get('amount')
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method')
            
            messages.success(request, f'Payment processed successfully for teacher.')
            return redirect('all_teachers')
            
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    teachers = Teacher.objects.filter(is_active=True)
    context = {
        'teachers': teachers,
    }
    return render(request, 'teachers/teacher_payment.html', context)

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
def expense_detail(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    
    context = {
        'expense': expense
    }
    return render(request, 'finances/expense_detail.html', context)

# AJAX view for expense statistics
@login_required
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
@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

def mark_paid(request, fee_id):
    """Mark a single fee as paid"""
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

@login_required
def fee_detail(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    context = {
        'fee': fee
    }
    return render(request, 'finances/fees/fee_detail.html', context)

@login_required
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

@login_required
def mark_paid(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    if fee.status != 'paid':
        fee.status = 'paid'
        fee.paid_date = timezone.now().date()
        fee.save()
        messages.success(request, f'Fee "{fee.name}" has been marked as paid.')
    else:
        messages.warning(request, f'Fee "{fee.name}" is already paid.')
    return redirect('all_fees')

@login_required
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

@login_required
def messaging(request):
    if request.method == 'POST':
        try:
            receiver_id = request.POST.get('receiver')
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            
            if not receiver_id:
                messages.error(request, 'Please select a recipient.')
                return redirect('messaging')
            
            receiver = User.objects.get(id=receiver_id)
            
            # Create message with file handling
            message = Message(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                content=content
            )
            
            # Handle file upload
            if 'message_file' in request.FILES:
                message.file = request.FILES['message_file']
            
            message.save()
            
            messages.success(request, 'Message sent successfully!')
            return redirect('messaging')
            
        except User.DoesNotExist:
            messages.error(request, 'Selected recipient does not exist.')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
    
    # Get conversations logic
    conversations = get_conversations(request.user)
    
    # Get message counts for the dashboard cards
    sent_count = Message.objects.filter(sender=request.user).count()
    received_count = Message.objects.filter(receiver=request.user).count()
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    
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
    """AJAX view to send a message with file upload support"""
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
        
        # Handle file uploads - support multiple files
        files = request.FILES.getlist('file')  # Get list of files
        
        # For now, we'll only use the first file (you can modify this to support multiple files)
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
        
        response_data = {
            'success': True,
            'message': 'Message sent successfully!',
            'message_id': message.id,
            'sent_date': message.sent_date.strftime('%Y-%m-%d %H:%M')
        }
        
        # Add file info if file was uploaded
        if message.file:
            response_data['file_info'] = {
                'name': message.file.name.split('/')[-1],
                'url': message.file.url,
                'size': message.file.size
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

def get_conversations(user):
    """Helper function to get conversations for a user"""
    # Get unique users from sent and received messages
    sent_users = Message.objects.filter(sender=user).values_list('receiver', flat=True).distinct()
    received_users = Message.objects.filter(receiver=user).values_list('sender', flat=True).distinct()
    
    all_users = set(sent_users) | set(received_users)
    
    conversations = []
    for user_id in all_users:
        try:
            other_user = User.objects.get(id=user_id)
            latest_message = Message.objects.filter(
                models.Q(sender=user, receiver=other_user) | 
                models.Q(sender=other_user, receiver=user)
            ).order_by('-sent_date').first()
            
            unread_count = Message.objects.filter(
                sender=other_user,
                receiver=user,
                is_read=False
            ).count()
            
            user_type = get_user_type(other_user)
            
            # Check online status using the new function
            is_online = check_user_online(other_user)
            
            conversations.append({
                'user': other_user,
                'latest_message': latest_message,
                'unread_count': unread_count,
                'user_type': user_type,
                'is_online': is_online,
            })
        except User.DoesNotExist:
            continue
    
    # Sort by latest message date
    conversations.sort(key=lambda x: x['latest_message'].sent_date if x['latest_message'] else timezone.now(), reverse=True)
    return conversations

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

@login_required
@require_GET
def get_conversation_messages(request, user_id):
    """AJAX view to get messages for a specific conversation"""
    try:
        other_user = get_object_or_404(User, id=user_id)
        
        # Get messages between current user and the other user
        messages_qs = Message.objects.filter(
            models.Q(sender=request.user, receiver=other_user) | 
            models.Q(sender=other_user, receiver=request.user)
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
                'sent_date': msg.sent_date.strftime('%Y-%m-%d %H:%M'),
                'is_read': msg.is_read,
                'is_outgoing': msg.sender.id == request.user.id,
            }
            
            # Add file information if exists
            if msg.file:
                message_data['file_info'] = {
                    'name': msg.file.name.split('/')[-1],
                    'file_name': msg.file.name.split('/')[-1],
                    'file_url': msg.file.url,
                    'file_size': msg.file.size,
                    'file_type': 'unknown'  # You might want to detect this
                }
            
            messages_data.append(message_data)
        
        # Check if user is online using the new function
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
        return JsonResponse({
            'success': False,
            'error': str(e)
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
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()
            
            if hasattr(user, 'teacher'):
                teacher = user.teacher
                teacher.phone = request.POST.get('phone')
                teacher.address = request.POST.get('address')
                if 'photo' in request.FILES:
                    teacher.photo = request.FILES['photo']
                teacher.save()
            
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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
    
    context = {
        'parent': parent,
        'children': children,
    }
    return render(request, 'parents/parent_details.html', context)

@login_required
def add_parent(request):
    if request.method == 'POST':
        try:
            # Create parent user
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password1')
            
            parent_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name')
            )
            
            # Add to Parent group
            from django.contrib.auth.models import Group
            parent_group, created = Group.objects.get_or_create(name='Parent')
            parent_user.groups.add(parent_group)
            
            # Create parent profile
            parent = Parent.objects.create(
                user=parent_user,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                phone=request.POST.get('phone'),
                email=email,
                address=request.POST.get('address'),
                occupation=request.POST.get('occupation', ''),
                father_name=request.POST.get('father_name', ''),
                mother_name=request.POST.get('mother_name', ''),
            )
            
            # Link students if provided
            student_ids = request.POST.getlist('students')
            if student_ids:
                students = Student.objects.filter(id__in=student_ids)
                parent.students.set(students)
            
            messages.success(request, f'Parent {parent.full_name} added successfully!')
            messages.info(request, f'Parent login created: Username: {username}, Password: {password}')
            return redirect('parent_details', parent_id=parent.id)
            
        except Exception as e:
            messages.error(request, f'Error adding parent: {str(e)}')
    
    students = Student.objects.filter(is_active=True)
    context = {
        'students': students,
    }
    return render(request, 'parents/add_parent.html', context)

@login_required
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

@login_required
def export_results_csv(request, exam_id):
    """Export exam results to CSV format"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def manage_classes(request):
    """Manage all classes in the system"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    classes = Class.objects.all().order_by('grade_level', 'name')
    
    context = {
        'classes': classes,
    }
    return render(request, 'academic/manage_classes.html', context)

@login_required
def add_class(request):
    """Add a new class"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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
    
    context = {
        'form': form,
        'title': 'Add New Class'
    }
    return render(request, 'academic/class_form.html', context)

@login_required
def edit_class(request, class_id):
    """Edit an existing class"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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
    
    context = {
        'form': form,
        'title': 'Edit Class',
        'class_obj': class_obj
    }
    return render(request, 'academic/class_form.html', context)

@login_required
def delete_class(request, class_id):
    """Delete a class"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        class_name = class_obj.name
        class_obj.delete()
        messages.success(request, f'Class "{class_name}" deleted successfully!')
        return redirect('manage_classes')
    
    context = {
        'class_obj': class_obj
    }
    return render(request, 'academic/confirm_delete_class.html', context)

@login_required
def manage_subjects(request):
    """Manage all subjects in the system"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    subjects = Subject.objects.all().order_by('name')
    
    context = {
        'subjects': subjects,
    }
    return render(request, 'academic/manage_subjects.html', context)

@login_required
def add_subject(request):
    """Add a new subject"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def edit_subject(request, subject_id):
    """Edit an existing subject"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def delete_subject(request, subject_id):
    """Delete a subject"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def manage_timetable(request):
    """Manage class timetables"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    classes = Class.objects.all()
    selected_class_id = request.GET.get('class')
    
    timetable_data = []
    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id)
        # You would typically fetch timetable entries for this class
        # timetable_data = Timetable.objects.filter(class_level=selected_class).order_by('day', 'period')
    
    context = {
        'classes': classes,
        'selected_class_id': selected_class_id,
        'timetable_data': timetable_data,
    }
    return render(request, 'academic/manage_timetable.html', context)

@login_required
def generate_timetable(request):
    """Generate timetable automatically"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        # Implement timetable generation logic here
        messages.success(request, 'Timetable generated successfully!')
        return redirect('manage_timetable')
    
    classes = Class.objects.all()
    context = {
        'classes': classes,
    }
    return render(request, 'academic/generate_timetable.html', context)

@login_required
def class_timetable(request, class_id):
    """View timetable for a specific class"""
    class_obj = get_object_or_404(Class, id=class_id)
    
    # You would typically fetch timetable entries for this class
    # timetable_data = Timetable.objects.filter(class_level=class_obj).order_by('day', 'period')
    timetable_data = []  # Placeholder
    
    context = {
        'class_obj': class_obj,
        'timetable_data': timetable_data,
    }
    return render(request, 'academic/class_timetable.html', context)

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

@login_required
def add_book(request):
    """Add a new book to the library"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def edit_book(request, book_id):
    """Edit book information"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def delete_book(request, book_id):
    """Delete a book"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def borrow_book(request):
    """Borrow a book"""
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        student_id = request.POST.get('student_id')
        due_date = request.POST.get('due_date')
        
        try:
            book = get_object_or_404(Book, id=book_id)
            student = get_object_or_404(Student, id=student_id)
            
            if book.available_copies > 0:
                # Create borrowing record
                borrowing = BookBorrowing.objects.create(
                    book=book,
                    borrower=student.user,
                    borrowed_date=timezone.now().date(),
                    due_date=due_date,
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
    students = Student.objects.filter(is_active=True)
    
    context = {
        'books': books,
        'students': students,
    }
    return render(request, 'library/borrow_book.html', context)

@login_required
def return_book(request, borrow_id):
    """Return a borrowed book"""
    borrowing = get_object_or_404(BookBorrowing, id=borrow_id)
    
    if request.method == 'POST':
        try:
            # Update borrowing record
            borrowing.returned_date = timezone.now().date()
            borrowing.status = 'RETURNED'
            borrowing.save()
            
            # Update available copies
            book = borrowing.book
            book.available_copies += 1
            book.save()
            
            messages.success(request, f'Book "{book.title}" returned successfully!')
            
        except Exception as e:
            messages.error(request, f'Error returning book: {str(e)}')
    
    return redirect('all_books')

@login_required
def exam_schedule(request):
    """View exam schedule"""
    exams = Exam.objects.all().order_by('exam_date')
    
    # Filter by class or date
    class_filter = request.GET.get('class')
    date_filter = request.GET.get('date')
    
    if class_filter:
        exams = exams.filter(class_level_id=class_filter)
    
    if date_filter:
        exams = exams.filter(exam_date=date_filter)
    
    context = {
        'exams': exams,
        'classes': Class.objects.all(),
    }
    return render(request, 'examinations/exam_schedule.html', context)

@login_required
def create_exam_schedule(request):
    """Create exam schedule"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
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

@login_required
def exam_grades(request):
    """View and manage exam grading system"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # You would typically fetch grading system data here
    # grading_system = GradingSystem.objects.all()
    
    context = {
        # 'grading_system': grading_system,
    }
    return render(request, 'examinations/exam_grades.html', context)

@login_required
def setup_grading_system(request):
    """Setup exam grading system"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Implement grading system setup logic
        messages.success(request, 'Grading system setup successfully!')
        return redirect('exam_grades')
    
    return render(request, 'examinations/setup_grading.html', context)

@login_required
def transport_management(request):
    """Transport management dashboard"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Transport statistics
    total_vehicles = 0  # Vehicle.objects.count()
    total_routes = 0    # Route.objects.count()
    assigned_students = 0  # Student.objects.filter(transport_route__isnull=False).count()
    
    context = {
        'total_vehicles': total_vehicles,
        'total_routes': total_routes,
        'assigned_students': assigned_students,
    }
    return render(request, 'transport/transport_management.html', context)

@login_required
def transport_routes(request):
    """View transport routes"""
    # routes = Route.objects.all()
    routes = []  # Placeholder
    
    context = {
        'routes': routes,
    }
    return render(request, 'transport/transport_routes.html', context)

@login_required
def transport_vehicles(request):
    """View transport vehicles"""
    # vehicles = Vehicle.objects.all()
    vehicles = []  # Placeholder
    
    context = {
        'vehicles': vehicles,
    }
    return render(request, 'transport/transport_vehicles.html', context)

@login_required
def assign_transport(request):
    """Assign transport to students"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        route_id = request.POST.get('route_id')
        
        try:
            student = get_object_or_404(Student, id=student_id)
            # route = get_object_or_404(Route, id=route_id)
            # student.transport_route = route
            student.save()
            
            messages.success(request, f'Transport assigned to {student.full_name} successfully!')
            
        except Exception as e:
            messages.error(request, f'Error assigning transport: {str(e)}')
    
    students = Student.objects.filter(is_active=True)
    # routes = Route.objects.all()
    routes = []  # Placeholder
    
    context = {
        'students': students,
        'routes': routes,
    }
    return render(request, 'transport/assign_transport.html', context)

@login_required
def hostel_management(request):
    """Hostel management dashboard"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Hostel statistics
    total_rooms = 0  # HostelRoom.objects.count()
    total_capacity = 0  # HostelRoom.objects.aggregate(Sum('capacity'))['capacity__sum'] or 0
    occupied_beds = 0  # HostelAllocation.objects.filter(status='ACTIVE').count()
    
    context = {
        'total_rooms': total_rooms,
        'total_capacity': total_capacity,
        'occupied_beds': occupied_beds,
    }
    return render(request, 'hostel/hostel_management.html', context)

@login_required
def hostel_rooms(request):
    """View hostel rooms"""
    # rooms = HostelRoom.objects.all()
    rooms = []  # Placeholder
    
    context = {
        'rooms': rooms,
    }
    return render(request, 'hostel/hostel_rooms.html', context)

@login_required
def hostel_allocations(request):
    """View hostel allocations"""
    # allocations = HostelAllocation.objects.all().select_related('student', 'room')
    allocations = []  # Placeholder
    
    context = {
        'allocations': allocations,
    }
    return render(request, 'hostel/hostel_allocations.html', context)

@login_required
def allocate_hostel(request):
    """Allocate hostel to students"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        room_id = request.POST.get('room_id')
        
        try:
            student = get_object_or_404(Student, id=student_id)
            # room = get_object_or_404(HostelRoom, id=room_id)
            
            # Check if room has available beds
            # if room.available_beds > 0:
            #     allocation = HostelAllocation.objects.create(
            #         student=student,
            #         room=room,
            #         allocated_date=timezone.now().date(),
            #         status='ACTIVE'
            #     )
            #     
            #     room.available_beds -= 1
            #     room.save()
                
            messages.success(request, f'Hostel allocated to {student.full_name} successfully!')
            # else:
            #     messages.error(request, 'No available beds in selected room.')
            
        except Exception as e:
            messages.error(request, f'Error allocating hostel: {str(e)}')
    
    students = Student.objects.filter(is_active=True)
    # rooms = HostelRoom.objects.filter(available_beds__gt=0)
    rooms = []  # Placeholder
    
    context = {
        'students': students,
        'rooms': rooms,
    }
    return render(request, 'hostel/allocate_hostel.html', context)

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

@login_required
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
            
            parent.save()
            
            messages.success(request, f'Parent {parent.full_name} updated successfully!')
            return redirect('parent_details', parent_id=parent.id)
            
        except Exception as e:
            messages.error(request, f'Error updating parent: {str(e)}')
    
    context = {
        'parent': parent,
    }
    return render(request, 'parents/update_parent.html', context)

@login_required
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

@login_required
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
            teacher.phone = request.POST.get('phone', teacher.phone)
            teacher.email = request.POST.get('email', teacher.email)
            teacher.address = request.POST.get('address', teacher.address)
            teacher.qualification = request.POST.get('qualification', teacher.qualification)
            teacher.specialization = request.POST.get('specialization', teacher.specialization)
            teacher.experience = request.POST.get('experience', teacher.experience)
            teacher.salary = request.POST.get('salary', teacher.salary)
            
            if 'photo' in request.FILES:
                teacher.photo = request.FILES['photo']
            
            teacher.save()
            
            # Update subjects
            subject_ids = request.POST.getlist('subjects')
            teacher.subjects.set(subject_ids)
            
            messages.success(request, f'Teacher {teacher.full_name} updated successfully!')
            return redirect('teacher_details', teacher_id=teacher.teacher_id)
            
        except Exception as e:
            messages.error(request, f'Error updating teacher: {str(e)}')
    
    subjects = Subject.objects.all()
    context = {
        'teacher': teacher,
        'subjects': subjects,
    }
    return render(request, 'teachers/update_teacher.html', context)

@login_required
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

@login_required
def teacher_payment_detail(request, payment_id):
    """View teacher payment details"""
    # payment = get_object_or_404(TeacherPayment, id=payment_id)
    # context = {
    #     'payment': payment,
    # }
    # return render(request, 'teachers/teacher_payment_detail.html', context)
    messages.info(request, 'Teacher payment detail view will be implemented soon.')
    return redirect('teacher_payment')

@login_required
def add_teacher_payment(request):
    """Add teacher payment"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
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

@login_required
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
    """Edit an existing exam"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam, teacher=teacher)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Exam "{exam.name}" updated successfully!')
                return redirect('teacher_exam_management')
            except Exception as e:
                messages.error(request, f'Error updating exam: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamForm(instance=exam, teacher=teacher)
    
    context = {
        'form': form,
        'exam': exam,
        'teacher': teacher,
        'title': 'Edit Exam'
    }
    return render(request, 'teachers/exam_form.html', context)

@login_required
def delete_exam(request, exam_id):
    """Delete an exam"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    
    if request.method == 'POST':
        exam_name = exam.name
        exam.delete()
        messages.success(request, f'Exam "{exam_name}" deleted successfully!')
        return redirect('teacher_exam_management')
    
    context = {
        'exam': exam
    }
    return render(request, 'teachers/confirm_delete_exam.html', context)

@login_required
def export_results_csv(request, exam_id):
    """Export exam results to CSV format"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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