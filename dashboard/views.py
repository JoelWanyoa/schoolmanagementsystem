# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Count, Sum, Q
from core.models import *
from core.forms import ExpenseForm, FeeForm
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import traceback
import json
from django.core.paginator import Paginator
import random
import string
from core.consumer import check_user_online

from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied

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
        
        # Get teacher-specific data
        from django.utils import timezone
        from django.db.models import Count, Q
        from core.models import Class, ClassSchedule, Student, Attendance, Assignment
        
        today = timezone.now().date()
        
        # Teacher's classes
        teacher_classes = Class.objects.filter(class_teacher=teacher)
        teacher_subjects = teacher.subjects.all()
        
        # Today's schedule
        today_schedule = ClassSchedule.objects.filter(
            teacher=teacher,
            day_of_week=today.strftime('%A').upper()
        ).select_related('class_level', 'subject').order_by('start_time')
        
        # Students in teacher's classes
        total_students = Student.objects.filter(
            current_class__in=teacher_classes
        ).count()
        
        # Today's attendance for teacher's classes
        today_attendance = Attendance.objects.filter(
            student__current_class__in=teacher_classes,
            date=today
        )
        present_today = today_attendance.filter(status=True).count()
        absent_today = today_attendance.filter(status=False).count()
        
        # Assignments to grade
        assignments_to_grade = Assignment.objects.filter(
            subject__in=teacher_subjects,
            due_date__gte=today
        ).count()
        
        # Recent notices
        from core.models import Notice
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
        
        return render(request, 'dashboard/teacher_dashboard.html', context)
        
    except Exception as e:
        print(f"Teacher dashboard error: {e}")
        messages.error(request, "Error loading teacher dashboard.")
        return render(request, 'dashboard/teacher_dashboard.html', {})

# Helper function for parent dashboard
def get_parent_children(parent):
    """Helper function to get all children for a parent"""
    children = parent.students.filter(is_active=True)
    
    # If no children in direct relationship, try to find by guardian info
    if not children.exists():
        children = Student.objects.filter(
            Q(guardian_email=parent.email) | 
            Q(guardian_phone=parent.phone)
        ).filter(is_active=True).distinct()
        
        # Auto-link found children to parent
        for child in children:
            if child not in parent.students.all():
                parent.students.add(child)
    
    return children

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
            for student in students:
                student.current_class = new_class
                if new_section:
                    student.current_section = new_section
                student.save()
                
                # Update any existing fees for the student to the new academic year
                Fee.objects.filter(student=student).update(academic_year=academic_year)
                
                promoted_count += 1
            
            messages.success(request, f'Successfully promoted {promoted_count} students to {new_class.name} for academic year {academic_year.name}.')
            return redirect('all_students')
            
        except Exception as e:
            messages.error(request, f'Error promoting students: {str(e)}')
            print(f"Promotion error: {traceback.format_exc()}")
    
    students = Student.objects.filter(is_active=True)
    classes = Class.objects.all()
    sections = Section.objects.all()
    academic_years = AcademicYear.objects.all()
    
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
    }
    return render(request, 'students/student_promotion.html', context)

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
            Q(teacher_id__icontains=search_query)
        )
    
    context = {
        'teachers': teachers,
    }
    return render(request, 'teachers/all_teachers.html', context)

@login_required
def teacher_details(request, teacher_id):
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
    classes_taught = Class.objects.filter(class_teacher=teacher)
    
    context = {
        'teacher': teacher,
        'classes_taught': classes_taught,
    }
    return render(request, 'teachers/teacher_details.html', context)

@login_required
def add_teacher(request):
    if request.method == 'POST':
        try:
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password1'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name')
            )
            
            teacher = Teacher.objects.create(
                user=user,
                teacher_id=request.POST.get('teacher_id'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                gender=request.POST.get('gender'),
                date_of_birth=request.POST.get('date_of_birth'),
                address=request.POST.get('address'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email'),
                qualification=request.POST.get('qualification'),
                specialization=request.POST.get('specialization'),
                experience=request.POST.get('experience'),
                joining_date=request.POST.get('joining_date'),
                salary=request.POST.get('salary'),
                photo=request.FILES.get('photo')
            )
            
            subject_ids = request.POST.getlist('subjects')
            teacher.subjects.set(subject_ids)
            
            messages.success(request, f'Teacher {teacher.full_name} added successfully!')
            return redirect('all_teachers')
            
        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')
    
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
    }
    return render(request, 'teachers/add_teacher.html', context)

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
    class_stats = Student.objects.filter(is_active=True).values(
        'current_class__name'
    ).annotate(
        count=Count('id')
    ).order_by('current_class__name')
    
    gender_stats = Student.objects.filter(is_active=True).values(
        'gender'
    ).annotate(
        count=Count('id')
    )
    
    six_months_ago = timezone.now() - timedelta(days=180)
    admission_trends = Student.objects.filter(
        admission_date__gte=six_months_ago
    ).extra(
        {'month': "strftime('%%Y-%%m', admission_date)"}
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    admission_status = AdmissionForm.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'class_stats': class_stats,
        'gender_stats': gender_stats,
        'admission_trends': admission_trends,
        'admission_status': admission_status,
    }
    
    return render(request, 'dashboard/student_analytics.html', context)

@login_required
def financial_overview(request):
    # Calculate actual financial metrics from database
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    paid_expenses = Expense.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_expenses = Expense.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get monthly expense data for charts
    current_year = timezone.now().year
    monthly_data = []
    monthly_labels = []
    
    for month in range(1, 13):
        month_expenses = Expense.objects.filter(
            date__year=current_year, 
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_data.append(float(month_expenses))
        monthly_labels.append(datetime(current_year, month, 1).strftime('%b'))
    
    # Get expense by category data
    expense_categories = []
    category_data = []
    category_labels = []
    category_colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796']
    
    for i, (category_key, category_name) in enumerate(Expense.EXPENSE_TYPES):
        category_total = Expense.objects.filter(
            expense_type=category_key
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        if category_total > 0:
            expense_categories.append({
                'name': category_name,
                'color': category_colors[i % len(category_colors)]
            })
            category_data.append(float(category_total))
            category_labels.append(category_name)
    
    context = {
        'total_revenue': 50000,  # This would come from your revenue model
        'total_expenses': total_expenses,
        'paid_expenses': paid_expenses,
        'pending_expenses': pending_expenses,
        'net_profit': 50000 - total_expenses,
        'pending_payments': Expense.objects.filter(status='pending').count(),
        
        # Chart data
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_expenses': json.dumps(monthly_data),
        
        # Pie chart data
        'expense_categories': expense_categories,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'category_colors': json.dumps(category_colors[:len(category_labels)]),
        
        # Recent transactions
        'recent_transactions': Expense.objects.all().order_by('-date')[:10]
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