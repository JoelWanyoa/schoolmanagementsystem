# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def login_view(request):
    # If user is already authenticated, redirect to appropriate dashboard
    if request.user.is_authenticated:
        return redirect_to_role_dashboard(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # UPDATE: Set user online status to 1 (online)
            update_user_online_status(user, True)
            
            # Check if setup is required after login
            try:
                from .models import Class, Section, AcademicYear
                classes_exist = Class.objects.exists()
                sections_exist = Section.objects.exists()
                academic_years_exist = AcademicYear.objects.exists()
                
                setup_required = not (classes_exist and sections_exist and academic_years_exist)
                
                if setup_required and (user.is_staff or user.is_superuser):
                    # Only admins need to complete setup
                    return redirect('initial_setup')
                else:
                    # Redirect to role-specific dashboard
                    return redirect_to_role_dashboard(user)
                    
            except DatabaseError:
                # If database error, redirect to role-specific dashboard
                return redirect_to_role_dashboard(user)
                
        else:
            messages.error(request, 'Invalid username or password')
    
    # For GET requests, use a simple context without database queries
    context = {}
    return render(request, 'auth/login.html', context)

def redirect_to_role_dashboard(user):
    """Redirect user to their role-specific dashboard"""
    if hasattr(user, 'student'):
        return redirect('student_dashboard')
    elif hasattr(user, 'teacher'):
        return redirect('teacher_dashboard')
    elif hasattr(user, 'parent'):
        return redirect('parent_dashboard')
    elif user.is_staff or user.is_superuser:
        return redirect('dashboard')  # Admin dashboard
    else:
        # Fallback for users without specific roles
        return redirect('dashboard')

@login_required
def logout_view(request):
    # UPDATE: Set user online status to 0 (offline) before logout
    update_user_online_status(request.user, False)
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# ADD: Helper function to update online status
def update_user_online_status(user, is_online):
    """
    Update user's online status across different user types
    """
    try:
        # Convert boolean to integer (1 for online, 0 for offline)
        online_status = 1 if is_online else 0
        
        # Update the base User model if it has is_online field
        if hasattr(user, 'is_online'):
            user.is_online = online_status
            user.save(update_fields=['is_online'])
        
        # Update Student profile if exists
        if hasattr(user, 'student'):
            user.student.is_online = online_status
            user.student.save(update_fields=['is_online'])
        
        # Update Teacher profile if exists
        if hasattr(user, 'teacher'):
            user.teacher.is_online = online_status
            user.teacher.save(update_fields=['is_online'])
        
        # Update Parent profile if exists
        if hasattr(user, 'parent'):
            user.parent.is_online = online_status
            user.parent.save(update_fields=['is_online'])
            
        print(f"DEBUG: Updated online status for {user.username} to {online_status}")
        
    except Exception as e:
        print(f"DEBUG: Error updating online status for {user.username}: {e}")