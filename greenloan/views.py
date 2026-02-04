# import django
# from django.core.management import call_command
# try:
#     call_command('migrate', interactive=False)
#     call_command('collectstatic', interactive=False, clear=True)
#     call_command('loaddata loan_types', interactive=False)
# except Exception as e:
#     print("Migration failed:", e)


from django.http import HttpResponse
from django.core.management import call_command
from django.db.utils import OperationalError

def migrate_view(request):
    try:
        # Run migrations
        call_command('migrate', interactive=False)
        # collect static files
        call_command('collectstatic', interactive=False, clear=True)
        # load initial data
        call_command('loaddata', 'loan_types')
    except OperationalError as e:
        return HttpResponse(f"Database error: {e}", status=500)
    except Exception as e:
        return HttpResponse(f"Migration failed: {e}", status=500)

    return HttpResponse("Migrations ran successfully!")
