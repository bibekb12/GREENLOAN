"""
WSGI config for greenloan project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import django
from django.core.management import call_command

try:
    call_command('migrate', interactive=False)
    call_command('collectstatic', interactive=False, clear=True)
except Exception as e:
    print("Migration failed:", e)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenloan.settings')

application = get_wsgi_application()
