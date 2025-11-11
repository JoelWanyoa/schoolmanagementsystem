# core/simple_context_processors.py
def simple_setup_required(request):
    """
    Simple context processor that doesn't query the database
    """
    return {
        'setup_required': False,
        'classes_exist': True,
        'sections_exist': True,
        'academic_years_exist': True,
    }


# core/context_processors.py
def user_role(request):
    """Add user role information to template context"""
    context = {
        'is_admin': request.user.is_superuser or request.user.is_staff,
        'is_teacher': hasattr(request.user, 'teacher'),
        'is_student': hasattr(request.user, 'student'),
        'is_parent': hasattr(request.user, 'parent'),
    }
    return context