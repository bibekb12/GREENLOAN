import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "greenloan.settings")

# Ensure the project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import django

django.setup()

from greenloan.wsgi import application

app = application
