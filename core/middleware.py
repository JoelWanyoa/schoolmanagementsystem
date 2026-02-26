# core/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from .models import Class, Section, AcademicYear
from django.utils import timezone
from django.core.cache import cache
import re

class SetupRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define setup-related URLs that should always be accessible
        self.setup_urls = [
            '/dashboard/setup/',
            '/dashboard/setup/create-classes/',
            '/dashboard/setup/create-sections/', 
            '/dashboard/setup/create-academic-years/',
            '/dashboard/setup/complete/',
            '/logout/',
            '/admin/'
        ]

    def __call__(self, request):
        # Skip for static files and media
        if any(request.path.startswith(path) for path in ['/static/', '/media/', '/admin/']):
            return self.get_response(request)

        # Skip for anonymous users
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Skip if this is a setup-related URL
        if any(request.path.startswith(url) for url in self.setup_urls):
            return self.get_response(request)

        # Check if setup is required
        try:
            classes_exist = Class.objects.exists()
            academic_years_exist = AcademicYear.objects.exists()
            
            # Setup is complete if we have basic data
            setup_complete = classes_exist and academic_years_exist
            
            # If setup is not complete, redirect to setup page
            if not setup_complete:
                # Only redirect if we're not already going to setup
                if not request.path.startswith('/dashboard/setup/'):
                    return redirect('initial_setup')
                    
        except Exception as e:
            # If database isn't ready or there's an error, allow access
            print(f"Setup middleware error (non-critical): {e}")
            # Don't redirect on database errors
        
        return self.get_response(request)

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