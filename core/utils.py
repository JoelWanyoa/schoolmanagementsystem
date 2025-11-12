# core/utils.py
from django import forms
from django.core.exceptions import ValidationError
from PIL import Image
import os

def get_dynamic_queryset(model_class, user=None):
    """Get dynamic queryset based on user permissions"""
    if user and hasattr(user, 'teacher'):
        if model_class.__name__ == 'Class':
            from .models import Class
            return Class.objects.filter(class_teacher=user.teacher)
        elif model_class.__name__ == 'Subject':
            return user.teacher.subjects.all()
    return model_class.objects.all()

def validate_file_size(file, max_size_mb=10):
    """Validate file size"""
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'File size must be less than {max_size_mb}MB.')
    return file

def validate_image_dimensions(file, max_width=2000, max_height=2000):
    """Validate image dimensions"""
    try:
        image = Image.open(file)
        width, height = image.size
        if width > max_width or height > max_height:
            raise ValidationError(
                f'Image dimensions must be less than {max_width}x{max_height} pixels.'
            )
    except Exception as e:
        raise ValidationError(f'Invalid image file: {str(e)}')
    return file

def generate_student_id():
    """Generate unique student ID"""
    from django.utils import timezone
    from .models import Student
    
    year = timezone.now().year
    last_student = Student.objects.filter(admission_date__year=year).order_by('-id').first()
    
    if last_student:
        last_id = int(last_student.student_id.split('-')[-1])
        new_id = last_id + 1
    else:
        new_id = 1
    
    return f"STU-{year}-{new_id:04d}"

def generate_teacher_id():
    """Generate unique teacher ID"""
    from django.utils import timezone
    from .models import Teacher
    
    year = timezone.now().year
    last_teacher = Teacher.objects.filter(joining_date__year=year).order_by('-id').first()
    
    if last_teacher:
        last_id = int(last_teacher.teacher_id.split('-')[-1])
        new_id = last_id + 1
    else:
        new_id = 1
    
    return f"TCH-{year}-{new_id:04d}"

def check_user_online(user):
    """
    Check if user is online by checking the is_online field
    """
    try:
        # Check if user has is_online field
        if hasattr(user, 'is_online'):
            return bool(user.is_online)
        
        # Check user profiles
        if hasattr(user, 'student') and hasattr(user.student, 'is_online'):
            return bool(user.student.is_online)
        elif hasattr(user, 'teacher') and hasattr(user.teacher, 'is_online'):
            return bool(user.teacher.is_online)
        elif hasattr(user, 'parent') and hasattr(user.parent, 'is_online'):
            return bool(user.parent.is_online)
        
        return False
        
    except Exception as e:
        print(f"DEBUG: Error checking online status: {e}")
        return False

def get_user_type(user):
    """Helper function to get user type"""
    try:
        if hasattr(user, 'teacher'):
            return 'TEACHER'
        elif hasattr(user, 'student'):
            return 'STUDENT'
        elif hasattr(user, 'parent'):
            return 'PARENT'
        elif user.is_staff or user.is_superuser:
            return 'STAFF'
        return 'USER'
    except:
        return 'USER'

def calculate_exam_positions(exam):
    """Calculate positions for an exam based on marks"""
    from .models import ExamResult
    from decimal import Decimal
    
    results = ExamResult.objects.filter(exam=exam).order_by('-marks_obtained')
    
    position = 1
    prev_marks = None
    same_rank_count = 0
    
    for result in results:
        current_marks = result.marks_obtained
        
        if prev_marks is not None and current_marks == prev_marks:
            same_rank_count += 1
        else:
            position += same_rank_count
            same_rank_count = 1
        
        result.position = position
        result.save()
        prev_marks = current_marks

def get_parent_children(parent):
    """Helper function to get all children for a parent"""
    from .models import Student
    from django.db.models import Q
    
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

def send_fee_reminder_email(fee, request):
    """Send fee reminder email"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils import timezone
    
    subject = f'Fee Reminder: {fee.name} - {fee.student.current_class.name}'
    context = {
        'fee': fee,
        'student': fee.student,
        'today': timezone.now().date(),
    }
    
    html_message = render_to_string('emails/fee_reminder.html', context)
    plain_message = f"Dear Parent,\n\nThis is a reminder for the {fee.name} fee of {fee.amount} for {fee.student.full_name}. The due date is {fee.due_date}.\n\nThank you."
    
    if fee.student.guardian_email:
        try:
            send_mail(
                subject,
                plain_message,
                'noreply@school.edu',
                [fee.student.guardian_email],
                html_message=html_message,
                fail_silently=True,
            )
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    return False

def get_conversations(user):
    """Helper function to get conversations for a user"""
    from .models import Message
    from django.db.models import Q
    from django.utils import timezone
    
    # Get unique users from sent and received messages
    sent_users = Message.objects.filter(sender=user).values_list('receiver', flat=True).distinct()
    received_users = Message.objects.filter(receiver=user).values_list('sender', flat=True).distinct()
    
    all_users = set(sent_users) | set(received_users)
    
    conversations = []
    for user_id in all_users:
        try:
            from django.contrib.auth.models import User
            other_user = User.objects.get(id=user_id)
            latest_message = Message.objects.filter(
                Q(sender=user, receiver=other_user) | 
                Q(sender=other_user, receiver=user)
            ).order_by('-sent_date').first()
            
            unread_count = Message.objects.filter(
                sender=other_user,
                receiver=user,
                is_read=False
            ).count()
            
            user_type = get_user_type(other_user)
            
            # Check online status
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