from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get a value from a dictionary by key"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """Calculate percentage (value / arg * 100)"""
    try:
        if float(arg) == 0:
            return 0
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_class(value, arg):
    """Add a CSS class to a form field"""
    return value.as_widget(attrs={'class': arg})

@register.filter
def get_initials(full_name):
    """Get initials from full name (first and last name)"""
    if not full_name:
        return 'U'
    
    names = full_name.strip().split()
    if len(names) == 1:
        return names[0][0].upper()
    else:
        return (names[0][0] + names[-1][0]).upper()

@register.filter
def get_period_entry(schedule, day, period_number):
    """Get timetable entry for specific day and period number"""
    for entry in schedule:
        if entry.day == day and entry.period_number == period_number:
            return entry
    return None

@register.filter
def has_period(entries, period_number):
    """Check if any entry has the given period number"""
    if not entries:
        return False
    return any(str(entry.period_number) == str(period_number) for entry in entries)