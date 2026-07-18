import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "greenloan.settings")

import django
from django.core.management import call_command

django.setup()

try:
    call_command("migrate", interactive=False, verbosity=0)
except Exception:
    pass

from greenloan.wsgi import application

app = application
