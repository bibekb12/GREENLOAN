from django.views.generic import ListView,TemplateView
from .models import SitePage

class IndexView(ListView):
    """This views return the index page for the application"""
    model = SitePage
    template_name = 'core/index.html'