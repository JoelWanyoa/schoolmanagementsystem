# create_admin.py
#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from django.contrib.auth.models import User, Group
from core.models import Teacher

def create_admin_user():
    """Create admin user with proper permissions"""
    
    print("=" * 60)
    print("SCHOOL MANAGEMENT SYSTEM - ADMIN CREATOR")
    print("=" * 60)
    
    # Admin details
    print("\nEnter admin details (press Enter for defaults):")
    
    username = input("Username [admin]: ").strip() or "admin"
    email = input("Email [admin@petra.edu]: ").strip() or "admin@petra.edu"
    password = input("Password [admin123]: ").strip() or "admin123"
    first_name = input("First Name [System]: ").strip() or "System"
    last_name = input("Last Name [Administrator]: ").strip() or "Administrator"
    
    create_teacher = input("\nCreate teacher profile? (y/n) [y]: ").strip().lower() or 'y'
    
    print("\n" + "=" * 60)
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        print(f"❌ User '{username}' already exists!")
        user = User.objects.get(username=username)
        display_user_info(user)
        return
    
    if User.objects.filter(email=email).exists():
        print(f"❌ User with email '{email}' already exists!")
        return
    
    try:
        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=True
        )
        
        # Add to admin group
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        user.groups.add(admin_group)
        
        print(f"✅ Admin user created successfully!")
        
        # Create teacher profile if requested
        if create_teacher in ['y', 'yes']:
            create_teacher_profile(user)
        
        display_user_info(user)
        
        # Save credentials
        save_credentials(username, password, email)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def create_teacher_profile(user):
    """Create teacher profile for admin"""
    try:
        if hasattr(user, 'teacher'):
            print("⚠️  Teacher profile already exists")
            return
        
        teacher = Teacher.objects.create(
            user=user,
            teacher_id=f"ADM-{datetime.now().year}-{user.id:04d}",
            first_name=user.first_name,
            last_name=user.last_name,
            gender='M',
            date_of_birth=datetime.now().date().replace(year=1980),
            address='School Address',
            phone='+1234567890',
            email=user.email,
            qualification='School Administrator',
            specialization='Administration',
            experience=5,
            joining_date=datetime.now().date(),
            salary=0,
            teaching_level='ALL',
            is_active=True
        )
        
        print(f"✅ Teacher profile created with ID: {teacher.teacher_id}")
        
    except Exception as e:
        print(f"❌ Error creating teacher profile: {str(e)}")

def display_user_info(user):
    """Display user information"""
    print("\n" + "-" * 60)
    print("USER INFORMATION:")
    print("-" * 60)
    print(f"Username:     {user.username}")
    print(f"Email:        {user.email}")
    print(f"Full Name:    {user.get_full_name()}")
    print(f"Superuser:    {user.is_superuser}")
    print(f"Staff:        {user.is_staff}")
    print(f"Groups:       {', '.join([g.name for g in user.groups.all()])}")
    
    if hasattr(user, 'teacher'):
        print(f"Teacher ID:   {user.teacher.teacher_id}")
    
    print("-" * 60)

def save_credentials(username, password, email):
    """Save credentials to file"""
    try:
        filename = f"admin_credentials_{username}.txt"
        with open(filename, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("ADMIN CREDENTIALS - KEEP SECURE!\n")
            f.write("=" * 60 + "\n")
            f.write(f"Username: {username}\n")
            f.write(f"Password: {password}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Login URL: http://localhost:8000/admin/\n")
            f.write("=" * 60 + "\n")
        
        print(f"\n📁 Credentials saved to: {filename}")
        print("⚠️  DELETE THIS FILE AFTER NOTING THE CREDENTIALS!")
        
    except Exception as e:
        print(f"⚠️  Could not save credentials file: {str(e)}")

if __name__ == "__main__":
    create_admin_user()