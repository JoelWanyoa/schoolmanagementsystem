# core/access_control.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# ===============================
# ROLE-BASED ACCESS CONTROL UTILITIES
# ===============================

def get_user_role(user):
    """
    Determine user role based on profile associations
    Returns: 'admin', 'teacher', 'student', 'parent', or 'user'
    """
    if user.is_superuser or user.is_staff:
        return 'admin'
    elif hasattr(user, 'teacher'):
        return 'teacher'
    elif hasattr(user, 'student'):
        return 'student'
    elif hasattr(user, 'parent'):
        return 'parent'
    else:
        return 'user'

def user_has_role(user, allowed_roles):
    """
    Check if user has one of the allowed roles
    """
    user_role = get_user_role(user)
    return user_role in allowed_roles

def can_access_dashboard(user):
    """
    Check if user can access the main admin dashboard
    """
    return user_has_role(user, ['admin'])

def can_access_teacher_dashboard(user):
    """
    Check if user can access teacher dashboard
    """
    return user_has_role(user, ['admin', 'teacher'])

def can_access_student_dashboard(user):
    """
    Check if user can access student dashboard
    """
    return user_has_role(user, ['admin', 'student'])

def can_access_parent_dashboard(user):
    """
    Check if user can access parent dashboard
    """
    return user_has_role(user, ['admin', 'parent'])

def can_manage_users(user):
    """
    Check if user can manage users (create, edit, delete)
    """
    return user_has_role(user, ['admin'])

def can_manage_academic_data(user):
    """
    Check if user can manage academic data (classes, subjects, timetable)
    """
    return user_has_role(user, ['admin'])

def can_manage_finances(user):
    """
    Check if user can manage financial data
    """
    return user_has_role(user, ['admin'])

def can_view_finances(user):
    """
    Check if user can view financial data (read-only)
    """
    return user_has_role(user, ['admin', 'teacher'])

def can_manage_students(user):
    """
    Check if user can manage students
    """
    return user_has_role(user, ['admin'])

def can_view_students(user):
    """
    Check if user can view students
    """
    return user_has_role(user, ['admin', 'teacher'])

def can_manage_teachers(user):
    """
    Check if user can manage teachers
    """
    return user_has_role(user, ['admin'])

def can_view_teachers(user):
    """
    Check if user can view teachers
    """
    return user_has_role(user, ['admin', 'teacher'])

def can_manage_parents(user):
    """
    Check if user can manage parents
    """
    return user_has_role(user, ['admin'])

def can_view_parents(user):
    """
    Check if user can view parents
    """
    return user_has_role(user, ['admin'])

def can_manage_attendance(user):
    """
    Check if user can manage attendance
    """
    return user_has_role(user, ['admin', 'teacher'])

def can_view_attendance(user):
    """
    Check if user can view attendance
    """
    return user_has_role(user, ['admin', 'teacher', 'student', 'parent'])

def can_manage_exams(user):
    """
    Check if user can manage exams
    """
    return user_has_role(user, ['admin', 'teacher'])

def can_view_exams(user):
    """
    Check if user can view exams
    """
    return user_has_role(user, ['admin', 'teacher', 'student', 'parent'])

def can_manage_assignments(user):
    """
    Check if user can manage assignments
    """
    return user_has_role(user, ['admin', 'teacher'])

def can_view_assignments(user):
    """
    Check if user can view assignments
    """
    return user_has_role(user, ['admin', 'teacher', 'student', 'parent'])

def can_send_messages(user):
    """
    Check if user can send messages
    """
    return user_has_role(user, ['admin', 'teacher', 'student', 'parent'])

def can_manage_library(user):
    """
    Check if user can manage library
    """
    return user_has_role(user, ['admin'])

def can_use_library(user):
    """
    Check if user can use library (borrow books)
    """
    return user_has_role(user, ['admin', 'teacher', 'student'])

# ===============================
# DATA ACCESS PERMISSIONS
# ===============================

def can_access_student_data(user, student_id=None):
    """
    Check if user can access specific student data
    """
    if user_has_role(user, ['admin']):
        return True
    
    if user_has_role(user, ['teacher']):
        # Teachers can access students in their classes
        from .models import Student, Class
        if student_id:
            student = Student.objects.filter(id=student_id).first()
            if student and student.current_class:
                return student.current_class.class_teacher == user.teacher
        return True
    
    if user_has_role(user, ['student']):
        # Students can only access their own data
        if student_id:
            return hasattr(user, 'student') and user.student.id == student_id
        return True
    
    if user_has_role(user, ['parent']):
        # Parents can access their children's data
        if student_id:
            return user.parent.students.filter(id=student_id).exists()
        return True
    
    return False

def can_access_teacher_data(user, teacher_id=None):
    """
    Check if user can access specific teacher data
    """
    if user_has_role(user, ['admin']):
        return True
    
    if user_has_role(user, ['teacher']):
        # Teachers can access their own data
        if teacher_id:
            return hasattr(user, 'teacher') and user.teacher.id == teacher_id
        return True
    
    # Students and parents can view teacher profiles
    return user_has_role(user, ['student', 'parent'])

def can_access_parent_data(user, parent_id=None):
    """
    Check if user can access specific parent data
    """
    if user_has_role(user, ['admin']):
        return True
    
    if user_has_role(user, ['parent']):
        # Parents can access their own data
        if parent_id:
            return hasattr(user, 'parent') and user.parent.id == parent_id
        return True
    
    return False

def can_access_class_data(user, class_id=None):
    """
    Check if user can access specific class data
    """
    if user_has_role(user, ['admin']):
        return True
    
    if user_has_role(user, ['teacher']):
        # Teachers can access their own classes
        from .models import Class
        if class_id:
            return Class.objects.filter(id=class_id, class_teacher=user.teacher).exists()
        return True
    
    if user_has_role(user, ['student']):
        # Students can access their own class
        if class_id and hasattr(user, 'student'):
            return user.student.current_class.id == class_id
        return True
    
    if user_has_role(user, ['parent']):
        # Parents can access classes of their children
        if class_id:
            return user.parent.students.filter(current_class_id=class_id).exists()
        return True
    
    return False

# ===============================
# DECORATORS FOR VIEW ACCESS CONTROL
# ===============================

def role_required(allowed_roles, redirect_url='dashboard', message=None):
    """
    Decorator to restrict view access based on user roles
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not user_has_role(request.user, allowed_roles):
                if not message:
                    default_messages = {
                        'admin': "This area is restricted to administrators only.",
                        'teacher': "This area is restricted to teachers only.",
                        'student': "This area is restricted to students only.",
                        'parent': "This area is restricted to parents only.",
                    }
                    # Use the first allowed role for the message
                    role_msg = default_messages.get(allowed_roles[0] if allowed_roles else 'admin', 
                                                   "You don't have permission to access this page.")
                    messages.error(request, role_msg)
                else:
                    messages.error(request, message)
                
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Specific role decorators
admin_required = role_required(['admin'])
teacher_required = role_required(['admin', 'teacher'])
student_required = role_required(['admin', 'student'])
parent_required = role_required(['admin', 'parent'])
staff_required = role_required(['admin', 'teacher'])  # Admin and teachers are considered staff

# Dashboard access decorators
def dashboard_redirect(view_func):
    """
    Decorator to redirect users to their appropriate dashboard
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user_role = get_user_role(request.user)
        
        # If user is already on their correct dashboard, proceed
        current_view = request.resolver_match.url_name
        correct_dashboard = {
            'admin': 'dashboard',
            'teacher': 'teacher_dashboard',
            'student': 'student_dashboard',
            'parent': 'parent_dashboard'
        }.get(user_role, 'login')
        
        if current_view != correct_dashboard:
            return redirect(correct_dashboard)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ===============================
# MIXIN FOR CLASS-BASED VIEWS
# ===============================

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin for class-based views to require specific roles
    """
    allowed_roles = []
    permission_denied_message = "You don't have permission to access this page."
    redirect_url = 'login'
    
    def test_func(self):
        return user_has_role(self.request.user, self.allowed_roles)
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)

class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']
    permission_denied_message = "This area is restricted to administrators only."

class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'teacher']
    permission_denied_message = "This area is restricted to teachers only."

class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'student']
    permission_denied_message = "This area is restricted to students only."

class ParentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'parent']
    permission_denied_message = "This area is restricted to parents only."

# ===============================
# CONTEXT PROCESSORS
# ===============================

def role_context(request):
    """
    Context processor to add role information to all templates
    """
    if request.user.is_authenticated:
        user_role = get_user_role(request.user)
        return {
            'user_role': user_role,
            'is_admin': user_role == 'admin',
            'is_teacher': user_role == 'teacher',
            'is_student': user_role == 'student',
            'is_parent': user_role == 'parent',
            'can_manage_users': can_manage_users(request.user),
            'can_manage_academic_data': can_manage_academic_data(request.user),
            'can_manage_finances': can_manage_finances(request.user),
        }
    return {}

# ===============================
# DASHBOARD REDIRECTION UTILITY
# ===============================

def get_user_dashboard_url(user):
    """
    Get the appropriate dashboard URL for a user based on their role
    """
    user_role = get_user_role(user)
    
    dashboard_urls = {
        'admin': 'dashboard',
        'teacher': 'teacher_dashboard', 
        'student': 'student_dashboard',
        'parent': 'parent_dashboard'
    }
    
    return dashboard_urls.get(user_role, 'login')

def redirect_to_user_dashboard(request):
    """
    Utility function to redirect user to their appropriate dashboard
    """
    dashboard_url = get_user_dashboard_url(request.user)
    return redirect(dashboard_url)

# ===============================
# PERMISSION CHECK UTILITIES FOR TEMPLATES
# ===============================

def template_has_permission(user, permission_type, object_id=None):
    """
    Utility function for template permission checks
    """
    permission_checks = {
        'manage_users': can_manage_users,
        'manage_academic': can_manage_academic_data,
        'manage_finances': can_manage_finances,
        'view_students': can_view_students,
        'manage_students': can_manage_students,
        'view_teachers': can_view_teachers,
        'manage_teachers': can_manage_teachers,
        'view_parents': can_view_parents,
        'manage_parents': can_manage_parents,
        'view_attendance': can_view_attendance,
        'manage_attendance': can_manage_attendance,
        'view_exams': can_view_exams,
        'manage_exams': can_manage_exams,
        'view_assignments': can_view_assignments,
        'manage_assignments': can_manage_assignments,
        'use_library': can_use_library,
        'manage_library': can_manage_library,
        'send_messages': can_send_messages,
    }
    
    if permission_type in permission_checks:
        return permission_checks[permission_type](user)
    
    # Data-specific permissions
    if permission_type == 'access_student_data':
        return can_access_student_data(user, object_id)
    elif permission_type == 'access_teacher_data':
        return can_access_teacher_data(user, object_id)
    elif permission_type == 'access_parent_data':
        return can_access_parent_data(user, object_id)
    elif permission_type == 'access_class_data':
        return can_access_class_data(user, object_id)
    
    return False