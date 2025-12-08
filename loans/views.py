from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView
from loans.forms import ApplicationForm
from loans.models import Application


# Create your views here.
class ApplyLoanView(LoginRequiredMixin,CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'loans/apply_loan.html'
