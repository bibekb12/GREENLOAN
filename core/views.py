from django.views.generic import ListView,TemplateView
from .models import SitePage
from loans.models import LoanTypes

class IndexView(ListView):
    """This views return the index page for the application"""
    model = SitePage
    context_object_name = 'LoanTypes'
    template_name = 'core/index.html'

    def get_queryset(self):
        return LoanTypes.objects.filter(is_active=True)
