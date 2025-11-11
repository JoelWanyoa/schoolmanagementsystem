# core/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from .models import Class, Section, AcademicYear
from django.utils import timezone
from django.core.cache import cache

# core/middleware.py - SIMPLER FIX
class SetupRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for static files, admin, auth, and setup pages
        excluded_paths = [
            '/static/', '/admin/', '/setup/', '/login/', '/logout/',
            '/password-reset/', '/api/', '/health/', '/dashboard/setup/complete/'
        ]
        
        if any(request.path.startswith(path) for path in excluded_paths):
            return self.get_response(request)

        # Skip for anonymous users
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Check if setup is required - BE LESS STRICT
        try:
            classes_exist = Class.objects.exists()
            academic_years_exist = AcademicYear.objects.exists()
            
            # Only require classes and academic years, not sections
            setup_complete = classes_exist and academic_years_exist
            
            # If NO data exists at all, then redirect to setup
            if (not classes_exist and not academic_years_exist and 
                not request.path.startswith('/setup/') and
                request.path != reverse('logout')):
                
                return redirect('initial_setup')
                
        except Exception as e:
            # If there's any database error, allow access
            print(f"Middleware error: {e}")
        
        response = self.get_response(request)
        return response
        # Skip for static files, admin, auth, and setup pages
        excluded_paths = [
            '/static/', '/admin/', '/setup/', '/login/', '/logout/',
            '/password-reset/', '/api/', '/health/'
        ]
        
        if any(request.path.startswith(path) for path in excluded_paths):
            return self.get_response(request)

        # Skip for anonymous users
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Check if setup is required
        try:
            classes_exist = Class.objects.exists()
            sections_exist = Section.objects.exists()
            academic_years_exist = AcademicYear.objects.exists()
            
            setup_complete = classes_exist and sections_exist and academic_years_exist
            
            # If setup is not complete and user is trying to access other pages, redirect to setup
            if (not setup_complete and 
                not request.path.startswith('/setup/') and
                request.path != reverse('logout')):
                
                # ADD THIS: Don't redirect if we're coming from complete_setup
                if not request.session.get('from_complete_setup', False):
                    return redirect('initial_setup')
                
        except Exception as e:
            # If there's any database error, allow access but log the error
            print(f"Middleware error: {e}")
        
        # Reset the flag
        if request.session.get('from_complete_setup'):
            del request.session['from_complete_setup']
            
        response = self.get_response(request)
        return response

class OnlineStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Update online status for authenticated users
        if request.user.is_authenticated:
            self.update_online_status(request.user)
        
        return response
    
    def update_online_status(self, user):
        """Update user's online status using cache as backup"""
        try:
            from .views import update_user_online_status
            update_user_online_status(user, True)
            
            # Also store in cache for real-time checks
            cache_key = f'user_online_{user.id}'
            cache.set(cache_key, True, timeout=300)  # 5 minutes timeout
            
        except Exception as e:
            print(f"DEBUG: Middleware online status error: {e}")