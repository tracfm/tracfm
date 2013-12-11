from django import template
register = template.Library()

"""
Simple tag let us define a regex for the active navigation tab
"""
@register.simple_tag
def active(request, pattern):
    import re
    
    if re.search(pattern, request.path):
        return 'active'
    return ''

"""
Check if string is in another string
"""
@register.filter
def value_in(value,arg):
    return value in arg