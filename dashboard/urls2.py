from django.urls import path, include

urlpatterns = [
    path('admin/', include('dashboard.urls_admin')),
    path('teacher/', include('dashboard.urls_teacher')),
    path('student/', include('dashboard.urls_student')),
    path('parent/', include('dashboard.urls_parent')),
]
