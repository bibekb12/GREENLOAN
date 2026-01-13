from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import update_session_auth_hash 
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from accounts.models import User
from loans.models import Application
from .forms import (
    KYCUpdateForm,
    SimpleUserCreationForm,
    EmailAuthenticationForm,
    UserProfileForm,
)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import get_object_or_404

"""this is class based view for the users """


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    form_class = EmailAuthenticationForm

    def get_success_url(self):
        return reverse("loans:landing")

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
    
class ChangePasswordView(PasswordChangeView):
    
    form_class = PasswordChangeForm
    template_name = 'resetpassword/change_password.html'
    success_url = reverse_lazy("accounts:dashboard")    



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
                    "pending_applications": Application.objects.filter(status="submitted").count(),
                    "pending_reviews": Application.objects.exclude(status="approved").count()
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
        user = request.user
        if "update_profile" in request.POST:
            form = UserProfileForm(request.POST, instance=request.user)

            if form.is_valid():
                form.save()
                return redirect(self.success_url)

        elif "update_kyc" in request.POST:
            kyc_form = KYCUpdateForm(request.POST, request.FILES, instance=user)
            has_existing_kyc = (user.citizenship_front_url and user.citizenship_back_url and user.passport_photo_url )

            if getattr(user,"kyc_status","pending") == "verified":
                messages.success(request,"Accounts already verified.")
                return redirect('accounts:profile') 

            if not request.FILES and not has_existing_kyc:
                messages.error(request,"Please upload required KYC documents.")
                return redirect('accounts:profile')

            if kyc_form.is_valid():
                user.kyc_status = "submitted"
                user.kyc_verified_at = None
                # Save uploaded files manually
                if request.FILES.get("citizenship_front"):
                    user.citizenship_front_url = request.FILES["citizenship_front"]
                if request.FILES.get("citizenship_back"):
                    user.citizenship_back_url = request.FILES["citizenship_back"]
                if request.FILES.get("passport_photo"):
                    user.passport_photo_url = request.FILES["passport_photo"]

                user.save()
                kyc_form.save()
                messages.success(request, "KYC updated successfully.")
                return redirect(self.success_url)
        return self.get(request, *args, **kwargs)


class KYCListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "accounts/kycapplication.html"
    context_object_name = "kyc_applications"

    def test_func(self):
        return self.request.user.role != "customer"

    def handle_no_permission(self):
        messages.error(
            self.request, "You don't have permission to view KYC applications."
        )
        return redirect("accounts:dashboard")

    def get_queryset(self):
        status = self.request.GET.get("status", "pending")
        return User.objects.filter(kyc_status=status)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "pending")
        return context


class VerifyKYCView(View):
    def test_func(self):
        return self.request.user.role != "customer"

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if "verify" in request.POST:
            user.kyc_status = "verified"
            user.kyc_verified_at = timezone.now()
            user.kyc_verified_by = request.user
        elif "reject" in request.POST:
            user.kyc_status = "rejected"
        elif "reverify" in request.POST:
            user.kyc_status = "submitted"
        user.save()
        return redirect(f"{reverse('accounts:kycapplication')}?status=submitted")
