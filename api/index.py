import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "greenloan.settings")

# Ensure the project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import django

django.setup()

# Run migrations silently on cold start (best-effort for SQLite on /tmp)
try:
    from django.core.management import call_command

    call_command("migrate", interactive=False, verbosity=0)
except Exception:
    pass

from greenloan.wsgi import application

app = application
