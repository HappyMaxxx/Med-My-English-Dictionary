import re
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def clean_word(word):
    return re.sub(r'[^\w\s]', '', word)

@register.filter
def range(value):
    return range(value)