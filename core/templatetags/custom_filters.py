from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get dictionary item by key"""
    return dictionary.get(key)


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