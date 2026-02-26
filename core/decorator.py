# core/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def login_required_custom(function=None, login_url=None):
    """
    Custom login_required decorator that doesn't conflict with custom User models
    """
    if function is None:
        return lambda func: login_required_custom(func, login_url=login_url)
    
    @wraps(function)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return function(request, *args, **kwargs)
        
        if login_url is None:
            from django.conf import settings
            login_url = settings.LOGIN_URL
        
        messages.error(request, "Please log in to access this page.")
        return redirect(login_url)
    
    return _wrapped_view

def admin_required(function=None):
    """Decorator for admin users"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            if not request.user.is_staff and not request.user.is_superuser:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator

def teacher_required(function=None):
    """Decorator for teacher users"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            if not hasattr(request.user, 'teacher'):
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator

def student_required(function=None):
    """Decorator for student users"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            if not hasattr(request.user, 'student'):
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator

def parent_required(function=None):
    """Decorator for parent users"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            if not hasattr(request.user, 'parent'):
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator