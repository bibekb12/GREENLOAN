from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect

from accounts.forms import SimpleUserCreationForm, UserProfileForm
from .models import SitePage
from loans.models import LoanTypes

User = get_user_model()


class IndexView(ListView):
    """This views return the index page for the application"""

    model = SitePage
    context_object_name = "LoanTypes"
    template_name = "core/index.html"

    def get_queryset(self):
        return LoanTypes.objects.filter(is_active=True)


class ContactView(TemplateView):
    template_name = "core/contact.html"


class SystemSettingsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/settings.html"

    def test_func(self):
        return self.request.user.role == "admin"


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "core/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def test_func(self):
        return self.request.user.role == "admin"

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.GET.get("role")
        if role:
            queryset = queryset.filter(role=role)
        return queryset


class AdminUserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = SimpleUserCreationForm
    template_name = "core/user_create.html"

    def test_func(self):
        return self.request.user.role == "admin"

    def handle_no_permission(self):
        messages.error(self.request, "You dont have permission.")
        return redirect("accounts:dashboard")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = self.request.POST.get("role", "customer")
        user.phone = self.request.POST.get("phone", "")
        user.save()

        messages.success(
            self.request,
            f"User {user.get_full_name() or user.username} created successfully.",
        )
        return redirect("accounts:user_list")
