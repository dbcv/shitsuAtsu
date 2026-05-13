import os
from django import template
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()

@register.simple_tag
def static_ts(path):
    static_url = staticfiles_storage.url(path)
    full_path = os.path.join(settings.BASE_DIR, 'static', path)
    if os.path.exists(full_path):
        timestamp = int(os.path.getmtime(full_path) * 1000)
        return f"{static_url}?v={timestamp}"
    return static_url