from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from accounts.models import User
from .forms import SimpleUserCreationForm, EmailAuthenticationForm, UserProfileForm
from django.contrib import messages


"""this is class based view for the users """
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    form_class = EmailAuthenticationForm

    def get_success_url(self):
        return reverse('accounts:dashboard')
    
    def form_invalid(self, form):
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('index')
    
class SignupView(CreateView):
    model = User
    form_class = SimpleUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'customer'
        user.phone = self.request.POST.get('phone','')
        user.save()

        #added the directly login after signup
        from django.contrib.auth import login
        login(self.request, user, backend='accounts.backends.EmailBackend')

        messages.success(self.request,"Account created succesfully.")
        return super().form_valid(form)
    

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_template_name(self):
        user = self.request.user
        if user.role == 'customer':
            return['accounts/customer_dashboard.html']

        elif user.role == 'admin':
            return['accounts/admin_dashboard.html']
        else:
            return['accounts/officer_dashboard.html']

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset
class AdminUserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = SimpleUserCreationForm
    template_name = 'accounts/user_create.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = self.request.POST.get('role','customer')
        user.phone = self.request.POST.get('phone','')
        user.save()

        messages.success(self.request, f'User {user.get_full_name() or user.username} created successfully.')
        return redirect('accounts:user_list')
    
class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
