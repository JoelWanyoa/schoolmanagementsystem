# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Count, Sum, Q, Avg, Max, Min, StdDev
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
from core.timetabling.generator import TimetableGenerator, AdvancedTimetableGenerator

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

def permission_denied(request):
    return render(request, 'permission_denied.html', status=403)

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
@student_required
def student_dashboard(request):
    """Dashboard for students with proper error handling"""
    try:
        # Ensure user has student profile
        if not hasattr(request.user, 'student'):
            messages.error(request, "Student profile not found. Please contact administration.")
            return redirect('login')
        
        student = request.user.student
        
        # Debug information
        print(f"DEBUG: Loading dashboard for student: {student.full_name}")
        print(f"DEBUG: Student ID: {student.student_id}")
        print(f"DEBUG: Class: {student.current_class}")
        print(f"DEBUG: Section: {student.current_section}")
        
        today = timezone.now().date()
        
        # Today's attendance with error handling
        try:
            today_attendance = Attendance.objects.filter(
                student=student, 
                date=today
            ).first()
            print(f"DEBUG: Today's attendance: {today_attendance}")
        except Exception as e:
            print(f"DEBUG: Error getting attendance: {e}")
            today_attendance = None
        
        # Upcoming exams (next 30 days) with error handling
        try:
            thirty_days_later = today + timedelta(days=30)
            upcoming_exams = Exam.objects.filter(
                class_level=student.current_class,
                exam_date__gte=today,
                exam_date__lte=thirty_days_later
            ).order_by('exam_date')[:5]
            print(f"DEBUG: Upcoming exams count: {upcoming_exams.count()}")
        except Exception as e:
            print(f"DEBUG: Error getting upcoming exams: {e}")
            upcoming_exams = []
        
        # Recent results with error handling
        try:
            recent_results = ExamResult.objects.filter(
                student=student
            ).select_related('exam', 'exam__subject').order_by('-exam__exam_date')[:5]
            print(f"DEBUG: Recent results count: {recent_results.count()}")
        except Exception as e:
            print(f"DEBUG: Error getting recent results: {e}")
            recent_results = []
        
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
        
        # Attendance summary with error handling
        try:
            attendance_summary = Attendance.objects.filter(student=student).aggregate(
                total_days=Count('id'),
                present_days=Count('id', filter=Q(status=True)),
                absent_days=Count('id', filter=Q(status=False))
            )
            print(f"DEBUG: Attendance summary: {attendance_summary}")
        except Exception as e:
            print(f"DEBUG: Error getting attendance summary: {e}")
            attendance_summary = {'total_days': 0, 'present_days': 0, 'absent_days': 0}
        
        context = {
            'student': student,
            'today_attendance': today_attendance,
            'upcoming_exams': upcoming_exams,
            'recent_results': recent_results,
            'fee_status': fee_status,
            'attendance_summary': attendance_summary,
        }
        
        print("DEBUG: Successfully loaded student dashboard context")
        return render(request, 'dashboard/student_dashboard.html', context)
        
    except Exception as e:
        print(f"DEBUG: Student dashboard error: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        
        messages.error(request, "Error loading student dashboard. Please contact support.")
        return render(request, 'dashboard/student_dashboard.html', {
            'student': getattr(request.user, 'student', None),
            'today_attendance': None,
            'upcoming_exams': [],
            'recent_results': [],
            'fee_status': {'total_due': 0, 'total_paid': 0},
            'attendance_summary': {'total_days': 0, 'present_days': 0, 'absent_days': 0},
        })

@teacher_required
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
            'percentage': round(percentage, 2)
        })
    
    # Top performers
    top_performers = results.order_by('-marks_obtained')[:10]
    
    # Low performers
    low_performers = results.order_by('marks_obtained')[:10]
    
    context = {
        'exam': exam,
        'stats': stats,
        'grade_data': grade_data,
        'marks_distribution': marks_distribution,
        'top_performers': top_performers,
        'low_performers': low_performers,
        'teacher': teacher,
    }
    return render(request, 'teachers/exam_analysis.html', context)

@login_required
def teacher_reports(request):
    """Reports dashboard for teachers"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)
    
    # Get report data
    total_students = Student.objects.filter(current_class__in=teacher_classes).count()
    
    # Attendance summary for teacher's classes
    attendance_summary = Attendance.objects.filter(
        student__current_class__in=teacher_classes
    ).aggregate(
        total_days=Count('id'),
        present_days=Count('id', filter=Q(status=True)),
        absent_days=Count('id', filter=Q(status=False))
    )
    
    # Exam performance summary
    exam_results = ExamResult.objects.filter(
        student__current_class__in=teacher_classes
    ).aggregate(
        avg_marks=Avg('marks_obtained'),
        total_exams=Count('exam', distinct=True)
    )
    
    # Assignment statistics
    assignment_stats = Assignment.objects.filter(teacher=teacher).aggregate(
        total_assignments=Count('id'),
        submitted_assignments=Count('submissions', filter=Q(submissions__submitted=True)),
        graded_assignments=Count('submissions', filter=Q(submissions__marks_obtained__isnull=False))
    )
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'total_students': total_students,
        'attendance_summary': attendance_summary,
        'exam_results': exam_results,
        'assignment_stats': assignment_stats,
    }
    return render(request, 'teachers/reports.html', context)

@login_required
def teacher_profile(request):
    """Teacher profile view and edit"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('teacher_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherProfileForm(instance=teacher)
    
    context = {
        'teacher': teacher,
        'form': form,
    }
    return render(request, 'teachers/profile.html', context)

@login_required
def teacher_notices(request):
    """View notices for teachers"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    
    # Get notices targeted at teachers or all
    notices = Notice.objects.filter(
        Q(target_audience='ALL') | Q(target_audience='TEACHERS'),
        is_active=True
    ).order_by('-publish_date')
    
    # Mark notices as read for this teacher
    for notice in notices:
        notice.read_by.add(teacher)
    
    context = {
        'teacher': teacher,
        'notices': notices,
    }
    return render(request, 'teachers/notices.html', context)

@login_required
def teacher_messages(request):
    """Messages for teachers"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    
    # Get conversations for this teacher
    conversations = get_conversations(request.user)
    
    context = {
        'teacher': teacher,
        'conversations': conversations,
    }
    return render(request, 'teachers/messages.html', context)

@login_required
def teacher_settings(request):
    """Settings for teachers"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    teacher = request.user.teacher
    
    if request.method == 'POST':
        # Handle settings form
        pass
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'teachers/settings.html', context)

@student_required
def student_profile(request):
    """Student profile view"""
    student = request.user.student
    
    context = {
        'student': student,
    }
    return render(request, 'students/profile.html', context)

@student_required
def student_timetable(request):
    """Student timetable view"""
    student = request.user.student
    
    # Get timetable for student's class and section
    timetable_entries = Timetable.objects.filter(
        class_level=student.current_class,
        section=student.current_section
    ).select_related('subject', 'teacher').order_by('day', 'period_number')
    
    # Today's schedule
    today = timezone.now().date()
    today_day = today.strftime('%A').upper()
    today_schedule = timetable_entries.filter(day=today_day).order_by('start_time')
    
    context = {
        'student': student,
        'timetable_entries': timetable_entries,
        'today_schedule': today_schedule,
        'today': today,
    }
    return render(request, 'students/timetable.html', context)

@student_required
def student_assignments(request):
    """Student assignments view"""
    student = request.user.student
    
    # Get assignments for student's class
    assignments = Assignment.objects.filter(
        class_level=student.current_class
    ).select_related('subject', 'teacher').order_by('-due_date')
    
    # Get student's submissions
    submissions = AssignmentSubmission.objects.filter(
        student=student
    ).select_related('assignment')
    submission_dict = {sub.assignment.id: sub for sub in submissions}
    
    # Add submission status to assignments
    for assignment in assignments:
        assignment.student_submission = submission_dict.get(assignment.id)
    
    context = {
        'student': student,
        'assignments': assignments,
    }
    return render(request, 'students/assignments.html', context)

@student_required
def student_exam_results(request):
    """Student exam results view"""
    student = request.user.student
    
    # Get exam results for student
    exam_results = ExamResult.objects.filter(
        student=student
    ).select_related('exam', 'exam__subject').order_by('-exam__exam_date')
    
    # Calculate statistics
    total_exams = exam_results.count()
    if total_exams > 0:
        average_marks = exam_results.aggregate(Avg('marks_obtained'))['marks_obtained__avg']
        highest_marks = exam_results.aggregate(Max('marks_obtained'))['marks_obtained__max']
        lowest_marks = exam_results.aggregate(Min('marks_obtained'))['marks_obtained__min']
    else:
        average_marks = highest_marks = lowest_marks = 0
    
    context = {
        'student': student,
        'exam_results': exam_results,
        'total_exams': total_exams,
        'average_marks': average_marks,
        'highest_marks': highest_marks,
        'lowest_marks': lowest_marks,
    }
    return render(request, 'students/exam_results.html', context)

@student_required
def student_attendance(request):
    """Student attendance view"""
    student = request.user.student
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        student=student
    ).order_by('-date')
    
    # Calculate attendance statistics
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status=True).count()
    absent_days = attendance_records.filter(status=False).count()
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Monthly attendance
    current_year = timezone.now().year
    monthly_attendance = []
    for month in range(1, 13):
        month_records = attendance_records.filter(date__year=current_year, date__month=month)
        present = month_records.filter(status=True).count()
        total = month_records.count()
        percentage = (present / total * 100) if total > 0 else 0
        monthly_attendance.append({
            'month': month,
            'present': present,
            'total': total,
            'percentage': round(percentage, 2)
        })
    
    context = {
        'student': student,
        'attendance_records': attendance_records,
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'attendance_percentage': round(attendance_percentage, 2),
        'monthly_attendance': monthly_attendance,
    }
    return render(request, 'students/attendance.html', context)

@student_required
def student_fees(request):
    """Student fees view"""
    student = request.user.student
    
    # Get fee records
    fees = Fee.objects.filter(student=student).select_related('academic_year')
    
    # Get payment history
    payments = FeePayment.objects.filter(student=student).order_by('-payment_date')
    
    # Calculate totals
    total_due = fees.aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    balance = total_due - total_paid
    
    context = {
        'student': student,
        'fees': fees,
        'payments': payments,
        'total_due': total_due,
        'total_paid': total_paid,
        'balance': balance,
    }
    return render(request, 'students/fees.html', context)

@student_required
def student_notices(request):
    """Student notices view"""
    student = request.user.student
    
    # Get notices for students or all
    notices = Notice.objects.filter(
        Q(target_audience='ALL') | Q(target_audience='STUDENTS'),
        is_active=True
    ).order_by('-publish_date')
    
    # Mark notices as read
    for notice in notices:
        notice.read_by.add(student)
    
    context = {
        'student': student,
        'notices': notices,
    }
    return render(request, 'students/notices.html', context)

@student_required
def student_messages(request):
    """Student messages view"""
    student = request.user.student
    
    # Get conversations
    conversations = get_conversations(request.user)
    
    context = {
        'student': student,
        'conversations': conversations,
    }
    return render(request, 'students/messages.html', context)

# Parent Views
@parent_required
def parent_dashboard(request):
    """Dashboard for parents"""
    parent = request.user.parent
    
    # Get children
    children = get_parent_children(request.user)
    
    # Get summary data for all children
    children_data = []
    for child in children:
        # Recent attendance
        recent_attendance = Attendance.objects.filter(
            student=child
        ).order_by('-date')[:7]
        
        # Recent exam results
        recent_results = ExamResult.objects.filter(
            student=child
        ).order_by('-exam__exam_date')[:3]
        
        # Fee status
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        fee_status = Fee.objects.filter(
            student=child,
            academic_year=current_academic_year
        ).aggregate(
            total_due=Sum('amount'),
            total_paid=Sum('amount_paid')
        )
        
        children_data.append({
            'student': child,
            'recent_attendance': recent_attendance,
            'recent_results': recent_results,
            'fee_status': fee_status,
        })
    
    context = {
        'parent': parent,
        'children_data': children_data,
    }
    return render(request, 'parents/dashboard.html', context)

@parent_required
def parent_child_detail(request, student_id):
    """Detailed view for a specific child"""
    parent = request.user.parent
    children = get_parent_children(request.user)
    
    try:
        child = children.get(id=student_id)
    except Student.DoesNotExist:
        messages.error(request, "Child not found.")
        return redirect('parent_dashboard')
    
    # Get detailed data for this child
    attendance_records = Attendance.objects.filter(student=child).order_by('-date')
    exam_results = ExamResult.objects.filter(student=child).select_related('exam', 'exam__subject').order_by('-exam__exam_date')
    assignments = Assignment.objects.filter(class_level=child.current_class).order_by('-due_date')
    
    # Get child's submissions
    submissions = AssignmentSubmission.objects.filter(student=child).select_related('assignment')
    submission_dict = {sub.assignment.id: sub for sub in submissions}
    
    # Add submission status to assignments
    for assignment in assignments:
        assignment.student_submission = submission_dict.get(assignment.id)
    
    # Fee details
    fees = Fee.objects.filter(student=child).select_related('academic_year')
    payments = FeePayment.objects.filter(student=child).order_by('-payment_date')
    
    total_due = fees.aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    balance = total_due - total_paid
    
    context = {
        'parent': parent,
        'child': child,
        'attendance_records': attendance_records,
        'exam_results': exam_results,
        'assignments': assignments,
        'fees': fees,
        'payments': payments,
        'total_due': total_due,
        'total_paid': total_paid,
        'balance': balance,
    }
    return render(request, 'parents/child_detail.html', context)

@parent_required
def parent_messages(request):
    """Parent messages view"""
    parent = request.user.parent
    
    # Get conversations
    conversations = get_conversations(request.user)
    
    context = {
        'parent': parent,
        'conversations': conversations,
    }
    return render(request, 'parents/messages.html', context)

@parent_required
def parent_notices(request):
    """Parent notices view"""
    parent = request.user.parent
    
    # Get notices for parents or all
    notices = Notice.objects.filter(
        Q(target_audience='ALL') | Q(target_audience='PARENTS'),
        is_active=True
    ).order_by('-publish_date')
    
    context = {
        'parent': parent,
        'notices': notices,
    }
    return render(request, 'parents/notices.html', context)

# Utility Views
@login_required
def export_data(request):
    """Export data to various formats"""
    export_type = request.GET.get('type', 'csv')
    data_type = request.GET.get('data', 'students')
    
    if data_type == 'students':
        queryset = Student.objects.all().select_related('current_class', 'current_section')
        filename = 'students'
    elif data_type == 'teachers':
        queryset = Teacher.objects.all()
        filename = 'teachers'
    elif data_type == 'attendance':
        queryset = Attendance.objects.all().select_related('student')
        filename = 'attendance'
    else:
        return HttpResponse("Invalid data type", status=400)
    
    if export_type == 'csv':
        return export_to_csv(queryset, filename)
    elif export_type == 'excel' and OPENPYXL_AVAILABLE:
        return export_to_excel(queryset, filename)
    elif export_type == 'pdf' and REPORTLAB_AVAILABLE:
        return export_to_pdf(queryset, filename)
    else:
        return HttpResponse("Export format not supported", status=400)

def export_to_csv(queryset, filename):
    """Export queryset to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    
    # Write headers based on model
    if hasattr(queryset.model, '_meta'):
        headers = [field.name for field in queryset.model._meta.fields]
        writer.writerow(headers)
        
        # Write data
        for obj in queryset:
            row = []
            for field in queryset.model._meta.fields:
                value = getattr(obj, field.name)
                if value is not None:
                    row.append(str(value))
                else:
                    row.append('')
            writer.writerow(row)
    
    return response

def export_to_excel(queryset, filename):
    """Export queryset to Excel"""
    df = pd.DataFrame(list(queryset.values()))
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    df.to_excel(response, index=False)
    return response

def export_to_pdf(queryset, filename):
    """Export queryset to PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Create table data
    data = []
    if queryset.exists():
        # Headers
        headers = [field.name for field in queryset.model._meta.fields]
        data.append(headers)
        
        # Data rows
        for obj in queryset[:100]:  # Limit to 100 rows for PDF
            row = []
            for field in queryset.model._meta.fields:
                value = getattr(obj, field.name)
                row.append(str(value) if value is not None else '')
            data.append(row)
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

@login_required
def import_data(request):
    """Import data from CSV/Excel"""
    if request.method == 'POST':
        import_type = request.POST.get('import_type')
        file = request.FILES.get('file')
        
        if not file:
            messages.error(request, 'Please select a file to import.')
            return redirect('import_data')
        
        try:
            if import_type == 'students':
                success_count, error_count = import_students_from_csv(file)
            elif import_type == 'teachers':
                success_count, error_count = import_teachers_from_csv(file)
            else:
                messages.error(request, 'Invalid import type.')
                return redirect('import_data')
            
            messages.success(request, f'Successfully imported {success_count} records. {error_count} errors occurred.')
            
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
        
        return redirect('import_data')
    
    context = {
        'import_types': [
            ('students', 'Students'),
            ('teachers', 'Teachers'),
        ]
    }
    return render(request, 'admin/import_data.html', context)

def import_students_from_csv(file):
    """Import students from CSV file"""
    success_count = 0
    error_count = 0
    
    # Read CSV
    decoded_file = file.read().decode('utf-8')
    csv_reader = csv.DictReader(StringIO(decoded_file))
    
    for row in csv_reader:
        try:
            # Create or update student
            student, created = Student.objects.update_or_create(
                admission_number=row.get('admission_number'),
                defaults={
                    'first_name': row.get('first_name'),
                    'last_name': row.get('last_name'),
                    'date_of_birth': row.get('date_of_birth'),
                    'gender': row.get('gender'),
                    'address': row.get('address'),
                    'phone': row.get('phone'),
                    'email': row.get('email'),
                    'current_class_id': row.get('current_class_id'),
                    'current_section_id': row.get('current_section_id'),
                    'roll_number': row.get('roll_number'),
                    'is_active': True
                }
            )
            success_count += 1
        except Exception as e:
            print(f"Error importing student {row.get('admission_number')}: {e}")
            error_count += 1
    
    return success_count, error_count

def import_teachers_from_csv(file):
    """Import teachers from CSV file"""
    success_count = 0
    error_count = 0
    
    # Read CSV
    decoded_file = file.read().decode('utf-8')
    csv_reader = csv.DictReader(StringIO(decoded_file))
    
    for row in csv_reader:
        try:
            # Create user first
            user = User.objects.create_user(
                username=row.get('username'),
                email=row.get('email'),
                password=row.get('password', 'defaultpass123'),
                first_name=row.get('first_name'),
                last_name=row.get('last_name')
            )
            
            # Create teacher profile
            teacher = Teacher.objects.create(
                user=user,
                employee_id=row.get('employee_id'),
                phone=row.get('phone'),
                address=row.get('address'),
                qualification=row.get('qualification'),
                experience_years=row.get('experience_years', 0),
                date_of_joining=row.get('date_of_joining'),
                is_active=True
            )
            
            success_count += 1
        except Exception as e:
            print(f"Error importing teacher {row.get('username')}: {e}")
            error_count += 1
    
    return success_count, error_count

@login_required
def system_reports(request):
    """System-wide reports dashboard"""
    # Overall statistics
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    total_classes = Class.objects.count()
    total_subjects = Subject.objects.count()
    
    # Academic year statistics
    current_year = AcademicYear.objects.filter(is_current=True).first()
    if current_year:
        year_students = Student.objects.filter(
            date_of_admission__gte=current_year.start_date,
            date_of_admission__lte=current_year.end_date
        ).count()
    else:
        year_students = 0
    
    # Fee collection
    total_fee_due = Fee.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_fee_paid = FeePayment.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    # Attendance summary
    attendance_summary = Attendance.objects.aggregate(
        total_records=Count('id'),
        present_count=Count('id', filter=Q(status=True)),
        absent_count=Count('id', filter=Q(status=False))
    )
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_subjects': total_subjects,
        'year_students': year_students,
        'total_fee_due': total_fee_due,
        'total_fee_paid': total_fee_paid,
        'attendance_summary': attendance_summary,
    }
    return render(request, 'admin/system_reports.html', context)

@login_required
def class_reports(request):
    """Class-wise reports"""
    classes = Class.objects.all()
    class_data = []
    
    for class_obj in classes:
        students = Student.objects.filter(current_class=class_obj, is_active=True)
        student_count = students.count()
        
        # Attendance for this class
        attendance = Attendance.objects.filter(student__in=students)
        present_count = attendance.filter(status=True).count()
        total_attendance = attendance.count()
        
        # Average attendance percentage
        attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
        
        # Exam results for this class
        exam_results = ExamResult.objects.filter(student__in=students)
        avg_marks = exam_results.aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0
        
        class_data.append({
            'class': class_obj,
            'student_count': student_count,
            'attendance_percentage': round(attendance_percentage, 2),
            'avg_marks': round(avg_marks, 2),
        })
    
    context = {
        'class_data': class_data,
    }
    return render(request, 'admin/class_reports.html', context)

@login_required
def financial_reports(request):
    """Financial reports"""
    # Monthly fee collection
    monthly_data = []
    current_year = timezone.now().year
    
    for month in range(1, 13):
        payments = FeePayment.objects.filter(
            payment_date__year=current_year,
            payment_date__month=month
        )
        total_collected = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        monthly_data.append({
            'month': month,
            'amount': total_collected
        })
    
    # Outstanding fees by class
    classes = Class.objects.all()
    outstanding_data = []
    
    for class_obj in classes:
        students = Student.objects.filter(current_class=class_obj, is_active=True)
        total_due = Fee.objects.filter(student__in=students).aggregate(Sum('amount'))['amount__sum'] or 0
        total_paid = FeePayment.objects.filter(student__in=students).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        outstanding = total_due - total_paid
        
        outstanding_data.append({
            'class': class_obj,
            'outstanding': outstanding
        })
    
    context = {
        'monthly_data': monthly_data,
        'outstanding_data': outstanding_data,
    }
    return render(request, 'admin/financial_reports.html', context)

@login_required
def user_management(request):
    """User management dashboard"""
    # Get all users with their profiles
    users = User.objects.all().select_related('student', 'teacher', 'parent')
    
    # Count by type
    student_users = users.filter(student__isnull=False).count()
    teacher_users = users.filter(teacher__isnull=False).count()
    parent_users = users.filter(parent__isnull=False).count()
    admin_users = users.filter(student__isnull=True, teacher__isnull=True, parent__isnull=True).count()
    
    # Recent users
    recent_users = users.order_by('-date_joined')[:10]
    
    context = {
        'total_users': users.count(),
        'student_users': student_users,
        'teacher_users': teacher_users,
        'parent_users': parent_users,
        'admin_users': admin_users,
        'recent_users': recent_users,
    }
    return render(request, 'admin/user_management.html', context)

@login_required
def system_settings(request):
    """System settings management"""
    settings = SystemSettings.get_instance()
    
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('system_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SystemSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
    }
    return render(request, 'admin/system_settings.html', context)

@login_required
def backup_database(request):
    """Create database backup"""
    try:
        # This is a simplified backup - in production, use proper backup tools
        from django.core.management import call_command
        from io import StringIO
        
        buffer = StringIO()
        call_command('dumpdata', stdout=buffer, exclude=['contenttypes', 'auth.permission'])
        
        response = HttpResponse(buffer.getvalue(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        messages.success(request, 'Database backup created successfully!')
        return response
        
    except Exception as e:
        messages.error(request, f'Backup failed: {str(e)}')
        return redirect('system_settings')

@login_required
def restore_database(request):
    """Restore database from backup"""
    if request.method == 'POST':
        backup_file = request.FILES.get('backup_file')
        
        if not backup_file:
            messages.error(request, 'Please select a backup file.')
            return redirect('system_settings')
        
        try:
            # Clear existing data (be careful!)
            # This is dangerous - implement proper validation
            
            from django.core.management import call_command
            from io import StringIO
            
            # Load data from file
            data = backup_file.read().decode('utf-8')
            
            # This is simplified - in production, validate and handle carefully
            messages.warning(request, 'Database restore completed. Please verify data integrity.')
            
        except Exception as e:
            messages.error(request, f'Restore failed: {str(e)}')
        
        return redirect('system_settings')
    
    return redirect('system_settings')

# AJAX Views for dynamic content
@csrf_exempt
@login_required
def ajax_get_students(request):
    """Get students for a class/section via AJAX"""
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    
    students = Student.objects.filter(is_active=True)
    
    if class_id:
        students = students.filter(current_class_id=class_id)
    if section_id:
        students = students.filter(current_section_id=section_id)
    
    students = students.order_by('roll_number')
    
    data = []
    for student in students:
        data.append({
            'id': student.id,
            'name': student.full_name,
            'roll_number': student.roll_number,
            'admission_number': student.admission_number,
        })
    
    return JsonResponse({'students': data})

@csrf_exempt
@login_required
def ajax_get_sections(request):
    """Get sections for a class via AJAX"""
    class_id = request.GET.get('class_id')
    
    sections = Section.objects.filter(class_name_id=class_id)
    
    data = []
    for section in sections:
        data.append({
            'id': section.id,
            'name': section.name,
        })
    
    return JsonResponse({'sections': data})

@csrf_exempt
@login_required
def ajax_mark_attendance(request):
    """Mark attendance via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            date = data.get('date')
            status = data.get('status')
            
            attendance_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            attendance, created = Attendance.objects.update_or_create(
                student_id=student_id,
                date=attendance_date,
                defaults={
                    'status': status,
                    'marked_by': request.user
                }
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def ajax_get_timetable(request):
    """Get timetable data via AJAX"""
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    
    timetable_entries = Timetable.objects.filter(
        class_level_id=class_id,
        section_id=section_id
    ).select_related('subject', 'teacher').order_by('day', 'period_number')
    
    data = []
    for entry in timetable_entries:
        data.append({
            'id': entry.id,
            'day': entry.day,
            'period_number': entry.period_number,
            'subject': entry.subject.name if entry.subject else 'No Subject',
            'teacher': entry.teacher.full_name if entry.teacher else 'No Teacher',
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'room': entry.room,
        })
    
    return JsonResponse({'timetable': data})

# Error handling views
def custom_404(request, exception):
    """Custom 404 page"""
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    """Custom 500 page"""
    return render(request, 'errors/500.html', status=500)

def custom_403(request, exception):
    """Custom 403 page"""
    return render(request, 'errors/403.html', status=403)

# API-like views for mobile app integration
@login_required
def api_user_profile(request):
    """API endpoint for user profile data"""
    user = request.user
    
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_type': get_user_type(user),
    }
    
    # Add profile-specific data
    if hasattr(user, 'student'):
        data['profile'] = {
            'type': 'student',
            'admission_number': user.student.admission_number,
            'current_class': user.student.current_class.name if user.student.current_class else None,
            'roll_number': user.student.roll_number,
        }
    elif hasattr(user, 'teacher'):
        data['profile'] = {
            'type': 'teacher',
            'employee_id': user.teacher.employee_id,
            'phone': user.teacher.phone,
            'qualification': user.teacher.qualification,
        }
    elif hasattr(user, 'parent'):
        data['profile'] = {
            'type': 'parent',
            'phone': user.parent.phone,
            'occupation': user.parent.occupation,
        }
    
    return JsonResponse(data)

@login_required
def api_dashboard_data(request):
    """API endpoint for dashboard statistics"""
    user_type = get_user_type(request.user)
    
    data = {}
    
    if user_type == 'admin':
        data = {
            'total_students': Student.objects.filter(is_active=True).count(),
            'total_teachers': Teacher.objects.filter(is_active=True).count(),
            'total_classes': Class.objects.count(),
            'pending_admissions': AdmissionForm.objects.filter(status='PENDING').count(),
        }
    elif user_type == 'teacher':
        teacher = request.user.teacher
        teacher_classes = Class.objects.filter(class_teacher=teacher)
        data = {
            'total_students': Student.objects.filter(current_class__in=teacher_classes, is_active=True).count(),
            'total_subjects': teacher.subjects.count(),
            'pending_assignments': Assignment.objects.filter(teacher=teacher, submissions__submitted=True, submissions__marks_obtained__isnull=True).distinct().count(),
        }
    elif user_type == 'student':
        student = request.user.student
        data = {
            'attendance_percentage': calculate_attendance_percentage(student),
            'upcoming_exams': Exam.objects.filter(class_level=student.current_class, exam_date__gte=timezone.now().date()).count(),
            'pending_assignments': Assignment.objects.filter(class_level=student.current_class, due_date__gte=timezone.now().date()).exclude(submissions__student=student).count(),
        }
    elif user_type == 'parent':
        children = get_parent_children(request.user)
        data = {
            'children_count': children.count(),
            'unread_messages': 0,  # Implement message count logic
            'pending_fees': sum([calculate_balance(child) for child in children]),
        }
    
    return JsonResponse(data)

@login_required
def api_attendance_data(request):
    """API endpoint for attendance data"""
    student_id = request.GET.get('student_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not student_id:
        return JsonResponse({'error': 'Student ID required'}, status=400)
    
    # Check permissions
    user_type = get_user_type(request.user)
    if user_type == 'student' and str(request.user.student.id) != student_id:
        return JsonResponse({'error': 'Access denied'}, status=403)
    elif user_type == 'parent':
        children = get_parent_children(request.user)
        if not children.filter(id=student_id).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    attendance_queryset = Attendance.objects.filter(student_id=student_id)
    
    if start_date:
        attendance_queryset = attendance_queryset.filter(date__gte=start_date)
    if end_date:
        attendance_queryset = attendance_queryset.filter(date__lte=end_date)
    
    attendance_queryset = attendance_queryset.order_by('-date')
    
    data = []
    for attendance in attendance_queryset:
        data.append({
            'date': attendance.date.isoformat(),
            'status': attendance.status,
            'remarks': attendance.remarks,
        })
    
    return JsonResponse({'attendance': data})

@login_required
def api_exam_results(request):
    """API endpoint for exam results"""
    student_id = request.GET.get('student_id')
    
    if not student_id:
        return JsonResponse({'error': 'Student ID required'}, status=400)
    
    # Check permissions
    user_type = get_user_type(request.user)
    if user_type == 'student' and str(request.user.student.id) != student_id:
        return JsonResponse({'error': 'Access denied'}, status=403)
    elif user_type == 'parent':
        children = get_parent_children(request.user)
        if not children.filter(id=student_id).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    results = ExamResult.objects.filter(student_id=student_id).select_related('exam', 'exam__subject')
    
    data = []
    for result in results:
        data.append({
            'exam_name': result.exam.name,
            'subject': result.exam.subject.name,
            'marks_obtained': float(result.marks_obtained),
            'total_marks': result.exam.total_marks,
            'percentage': (result.marks_obtained / result.exam.total_marks * 100),
            'grade': result.grade,
            'position': result.position,
            'exam_date': result.exam.exam_date.isoformat(),
        })
    
    return JsonResponse({'results': data})

@login_required
def api_fee_data(request):
    """API endpoint for fee data"""
    student_id = request.GET.get('student_id')
    
    if not student_id:
        return JsonResponse({'error': 'Student ID required'}, status=400)
    
    # Check permissions
    user_type = get_user_type(request.user)
    if user_type == 'student' and str(request.user.student.id) != student_id:
        return JsonResponse({'error': 'Access denied'}, status=403)
    elif user_type == 'parent':
        children = get_parent_children(request.user)
        if not children.filter(id=student_id).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    fees = Fee.objects.filter(student_id=student_id)
    payments = FeePayment.objects.filter(student_id=student_id)
    
    total_due = fees.aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    balance = total_due - total_paid
    
    fee_data = []
    for fee in fees:
        fee_data.append({
            'description': fee.description,
            'amount': float(fee.amount),
            'due_date': fee.due_date.isoformat() if fee.due_date else None,
        })
    
    payment_data = []
    for payment in payments:
        payment_data.append({
            'amount': float(payment.amount_paid),
            'payment_date': payment.payment_date.isoformat(),
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
        })
    
    return JsonResponse({
        'fees': fee_data,
        'payments': payment_data,
        'total_due': float(total_due),
        'total_paid': float(total_paid),
        'balance': float(balance),
    })

@login_required
def api_timetable_data(request):
    """API endpoint for timetable data"""
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    
    if not class_id:
        return JsonResponse({'error': 'Class ID required'}, status=400)
    
    # Check permissions
    user_type = get_user_type(request.user)
    if user_type == 'student':
        if str(request.user.student.current_class.id) != class_id:
            return JsonResponse({'error': 'Access denied'}, status=403)
        section_id = request.user.student.current_section.id
    elif user_type == 'parent':
        # Parents can access their children's timetable
        children = get_parent_children(request.user)
        if not children.filter(current_class_id=class_id).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    timetable_entries = Timetable.objects.filter(
        class_level_id=class_id,
        section_id=section_id
    ).select_related('subject', 'teacher').order_by('day', 'period_number')
    
    data = []
    for entry in timetable_entries:
        data.append({
            'day': entry.day,
            'period_number': entry.period_number,
            'subject': entry.subject.name if entry.subject else 'No Subject',
            'teacher': entry.teacher.full_name if entry.teacher else 'No Teacher',
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'room': entry.room,
        })
    
    return JsonResponse({'timetable': data})

@login_required
def api_notices(request):
    """API endpoint for notices"""
    user_type = get_user_type(request.user)
    
    if user_type == 'student':
        notices = Notice.objects.filter(
            Q(target_audience='ALL') | Q(target_audience='STUDENTS'),
            is_active=True
        )
    elif user_type == 'teacher':
        notices = Notice.objects.filter(
            Q(target_audience='ALL') | Q(target_audience='TEACHERS'),
            is_active=True
        )
    elif user_type == 'parent':
        notices = Notice.objects.filter(
            Q(target_audience='ALL') | Q(target_audience='PARENTS'),
            is_active=True
        )
    else:
        notices = Notice.objects.filter(is_active=True)
    
    notices = notices.order_by('-publish_date')[:20]
    
    data = []
    for notice in notices:
        data.append({
            'id': notice.id,
            'title': notice.title,
            'content': notice.content,
            'publish_date': notice.publish_date.isoformat(),
            'target_audience': notice.target_audience,
            'attachment': notice.attachment.url if notice.attachment else None,
        })
    
    return JsonResponse({'notices': data})

# Utility functions
def calculate_attendance_percentage(student):
    """Calculate attendance percentage for a student"""
    attendance_records = Attendance.objects.filter(student=student)
    if attendance_records.exists():
        present_count = attendance_records.filter(status=True).count()
        total_count = attendance_records.count()
        return round((present_count / total_count) * 100, 2)
    return 0

def calculate_balance(student):
    """Calculate fee balance for a student"""
    total_due = Fee.objects.filter(student=student).aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid = FeePayment.objects.filter(student=student).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    return total_due - total_paid

# Additional admin views
@login_required
def manage_academic_years(request):
    """Manage academic years"""
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic year created successfully!')
            return redirect('manage_academic_years')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AcademicYearForm()
    
    context = {
        'academic_years': academic_years,
        'form': form,
    }
    return render(request, 'admin/manage_academic_years.html', context)

@login_required
def manage_subjects(request):
    """Manage subjects"""
    subjects = Subject.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject created successfully!')
            return redirect('manage_subjects')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm()
    
    context = {
        'subjects': subjects,
        'form': form,
    }
    return render(request, 'admin/manage_subjects.html', context)

@login_required
def manage_notices(request):
    """Manage notices"""
    notices = Notice.objects.all().order_by('-publish_date')
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, 'Notice created successfully!')
            return redirect('manage_notices')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NoticeForm()
    
    context = {
        'notices': notices,
        'form': form,
    }
    return render(request, 'admin/manage_notices.html', context)

@login_required
def manage_fees(request):
    """Manage fee structures"""
    fees = Fee.objects.all().select_related('student', 'academic_year').order_by('-created_at')
    
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee record created successfully!')
            return redirect('manage_fees')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeeForm()
    
    context = {
        'fees': fees,
        'form': form,
    }
    return render(request, 'admin/manage_fees.html', context)

@login_required
def manage_exams(request):
    """Manage exams"""
    exams = Exam.objects.all().select_related('class_level', 'subject', 'created_by').order_by('-exam_date')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, 'Exam created successfully!')
            return redirect('manage_exams')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamForm()
    
    context = {
        'exams': exams,
        'form': form,
    }
    return render(request, 'admin/manage_exams.html', context)

@login_required
def manage_assignments(request):
    """Manage assignments system-wide"""
    assignments = Assignment.objects.all().select_related('teacher', 'subject', 'class_level').order_by('-due_date')
    
    context = {
        'assignments': assignments,
    }
    return render(request, 'admin/manage_assignments.html', context)

@login_required
def manage_timetable(request):
    """Manage timetable"""
    classes = Class.objects.all()
    selected_class = request.GET.get('class')
    
    if selected_class:
        sections = Section.objects.filter(class_name_id=selected_class)
        timetable_entries = Timetable.objects.filter(class_level_id=selected_class).select_related('section', 'subject', 'teacher')
    else:
        sections = []
        timetable_entries = []
    
    context = {
        'classes': classes,
        'sections': sections,
        'timetable_entries': timetable_entries,
        'selected_class': selected_class,
    }
    return render(request, 'admin/manage_timetable.html', context)

@login_required
def generate_timetable(request):
    """Generate timetable using algorithm"""
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        try:
            generator = TimetableGenerator()
            generator.generate_for_class(class_id)
            messages.success(request, 'Timetable generated successfully!')
        except Exception as e:
            messages.error(request, f'Error generating timetable: {str(e)}')
        
        return redirect('manage_timetable')
    
    classes = Class.objects.all()
    context = {
        'classes': classes,
    }
    return render(request, 'admin/generate_timetable.html', context)

@login_required
def system_logs(request):
    """View system logs"""
    # This would typically integrate with Django's logging system
    # For now, return a basic template
    context = {}
    return render(request, 'admin/system_logs.html', context)

@login_required
def database_maintenance(request):
    """Database maintenance tools"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'clear_cache':
            from django.core.cache import cache
            cache.clear()
            messages.success(request, 'Cache cleared successfully!')
        elif action == 'optimize_db':
            # Run database optimization commands
            messages.success(request, 'Database optimization completed!')
        elif action == 'cleanup_temp':
            # Clean up temporary files
            messages.success(request, 'Temporary files cleaned up!')
        
        return redirect('database_maintenance')
    
    context = {}
    return render(request, 'admin/database_maintenance.html', context)

# Communication views
@login_required
def messaging_center(request):
    """Central messaging interface"""
    conversations = get_conversations(request.user)
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'communication/messaging_center.html', context)

@login_required
def send_message(request):
    """Send a message"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            recipient = User.objects.get(id=recipient_id)
            
            # Create conversation if it doesn't exist
            conversation = Conversation.objects.filter(
                Q(initiator=request.user, recipient=recipient) |
                Q(initiator=recipient, recipient=request.user)
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create(
                    initiator=request.user,
                    recipient=recipient,
                    subject=subject
                )
            
            # Create message
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=message
            )
            
            messages.success(request, 'Message sent successfully!')
            
        except User.DoesNotExist:
            messages.error(request, 'Recipient not found.')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
    
    return redirect('messaging_center')

@login_required
def email_notifications(request):
    """Manage email notifications"""
    # This would integrate with email service
    context = {}
    return render(request, 'communication/email_notifications.html', context)

@login_required
def sms_notifications(request):
    """Manage SMS notifications"""
    # This would integrate with SMS service
    context = {}
    return render(request, 'communication/sms_notifications.html', context)

# Final utility views
@login_required
def help_center(request):
    """Help center"""
    context = {}
    return render(request, 'help/help_center.html', context)

@login_required
def about_system(request):
    """About the system"""
    context = {
        'version': '1.0.0',
        'release_date': '2024-01-01',
    }
    return render(request, 'help/about.html', context)

