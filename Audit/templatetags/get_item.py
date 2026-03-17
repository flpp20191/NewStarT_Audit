# Source - https://stackoverflow.com/a/8000091
# Posted by culebrón, modified by community. See post 'Timeline' for change history
# Retrieved 2026-02-03, License - CC BY-SA 4.0

from django.template.defaulttags import register

@register.filter
def get_item(dictionary: dict | list, key):
    if isinstance(dictionary, list):
        try: return dictionary[int(key)]
        except IndexError: return None
        except ValueError: return None
    return dictionary.get(key)
