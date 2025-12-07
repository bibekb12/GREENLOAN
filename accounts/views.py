from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, TemplateView

from accounts.models import User
from .forms import SimpleUserCreationForm, EmailAuthenticationForm
from django.contrib import messages


"""this is class based view for the users """
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    form_class = EmailAuthenticationForm

    def get_success_url(self):
        return reverse('accounts:dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request,'Invalid credentials provided.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('index')
    
class SignupView(CreateView):
    model = User
    form_class = SimpleUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:Dashboard')

    def form_valid(self, form):
        user = form.save()
        user.role = 'customer'
        user.phone = self.request.POST.get('phone','')
        user.save()

        #added the directly login after signup
        from django.contrib.auth import login
        login(self.request, user)

        messages.SUCCESS(self.request,"Account created succesfully.")
        return super().form_valid(form)
    

    
