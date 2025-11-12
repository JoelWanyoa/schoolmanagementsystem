from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get a value from a dictionary by key"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value


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