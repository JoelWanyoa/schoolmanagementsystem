# In your templatetags/user_tags.py
from django import template

register = template.Library()

@register.filter
def is_teacher(user):
    return hasattr(user, 'teacher')

@register.filter
def is_student(user):
    return hasattr(user, 'student')

@register.filter
def is_parent(user):
    return hasattr(user, 'parent')