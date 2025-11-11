# core/context_processors.py
from .models import *

def setup_required(request):
    """Check if initial setup is required"""
    classes_exist = Class.objects.exists()
    sections_exist = Section.objects.exists()
    academic_years_exist = AcademicYear.objects.exists()
    
    setup_complete = classes_exist and sections_exist and academic_years_exist
    
    return {
        'setup_required': not setup_complete,
        'classes_exist': classes_exist,
        'sections_exist': sections_exist,
        'academic_years_exist': academic_years_exist,
    }

# core/context_processors.py
def user_role(request):
    """Add user role information to template context"""
    if not request.user.is_authenticated:
        return {
            'is_admin': False,
            'is_teacher': False,
            'is_student': False,
            'is_parent': False,
        }
    
    return {
        'is_admin': request.user.is_superuser or request.user.is_staff,
        'is_teacher': hasattr(request.user, 'teacher'),
        'is_student': hasattr(request.user, 'student'),
        'is_parent': hasattr(request.user, 'parent'),
    }