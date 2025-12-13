from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from accounts.models import User
from loans.models import Application
from .forms import (
    KYCUpdateForm,
    SimpleUserCreationForm,
    EmailAuthenticationForm,
    UserProfileForm,
)
from django.contrib import messages


"""this is class based view for the users """


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    form_class = EmailAuthenticationForm

    def get_success_url(self):
        return reverse("accounts:dashboard")

    def form_invalid(self, form):
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("core:index")


class SignupView(CreateView):
    model = User
    form_class = SimpleUserCreationForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:dashboard")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = "customer"
        user.phone = self.request.POST.get("phone", "")
        user.save()

        # added the directly login after signup
        from django.contrib.auth import login

        login(self.request, user)

        messages.success(self.request, "Account created succesfully.")
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    # template_name = 'accounts/dashboard.html'

    def get_template_names(self):
        user = self.request.user
        if user.role == "customer":
            return ["accounts/customer_dashboard.html"]
        elif user.role == "admin":
            return ["accounts/admin_dashboard.html"]
        else:
            return ["accounts/officer_dashboard.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role in ["officer", "senior_officer", "admin"]:
            context.update(
                {
                    "applications": Application.objects.all()[:10],
                    "users": User.objects.all()[:10],
                    "total_applications": Application.objects.count(),
                    "pending_applications": Application.objects.filter(
                        status="submitted"
                    ).count(),
                }
            )
        elif user.role in ["loan_officer", "senior_officer"]:
            context.update(
                {
                    "applications": Application.objects.filter(officer=user),
                    "pending_reviews": Application.objects.filter(
                        officer=user, status="under_review"
                    ).count(),
                }
            )
        else:
            context.update(
                {
                    "applications": Application.objects.filter(applicant=user),
                }
            )
        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "accounts/profile.html"
    success_url = "/app/profile/"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = UserProfileForm(instance=self.request.user)
        context["kyc_form"] = KYCUpdateForm(instance=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        if "update_profile" in request.POST:
            form = UserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
        elif "update_kyc" in request.POST:
            kyc_form = KYCUpdateForm(request.POST, request.FILES, instance=request.user)
            if kyc_form.is_valid():
                kyc_form.save()
        return self.get(request, *args, **kwargs)
