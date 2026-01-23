from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))

@register.filter
def get_item_key(dictionary, key):
    return dictionary.get(str(key), {})

@register.filter
def get_val(dictionary, key):
    return dictionary.get(key)