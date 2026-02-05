from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
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

from accounts.tokens import email_verification_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_decode


"""this is class based view for the users """


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    form_class = EmailAuthenticationForm

    def get_success_url(self):
        return reverse("loans:landing")
    
    def form_valid(self, form):
        user = form.get_user()
        if user is not None and not user.email_verified:
                return render(self.request, "accounts/emailverify.html", {"email": user.email})
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Incorrect email or password")
        return self.render_to_response(self.get_context_data(form=form))


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
        user.is_active = True
        user.save()

        # sending verification email msg
        EmailAddrVerify.send_verification_email(self.request, user)

        messages.success(self.request, "Account created succesfully.")
        return super().form_valid(form)
    
class ChangePasswordView(PasswordChangeView):
    
    form_class = PasswordChangeForm
    template_name = 'resetpassword/change_password.html'
    success_url = reverse_lazy("accounts:dashboard")

class EmailAddrVerify(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            print("user")
            print("uid")
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and email_verification_token.check_token(user, token):
            user.is_active = True
            user.email_verified = True
            user.save()
            messages.success(request, "Your email has been verified successfully!")
        else:
            messages.error(request, "Invalid or expired verification link.")

        return redirect("accounts:login")

    @staticmethod
    def send_verification_email(request, user):
        token = email_verification_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = request.build_absolute_uri(reverse("accounts:email-verify", kwargs={'uidb64': uid, 'token': token}))

        subject = "Verify Your Email Address"
        message = f"""
        Hello {user.get_full_name()},

        Please verify your email by clicking the link below:

        {verification_url}

        Thank you!
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )    

class ResendEmailAddrVerify(View):
    def get(self, request):
        email = request.GET.get("email")
        if not email:
            messages.error(request,"No email address provided.")
            return redirect("accounts:login")
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                messages.info(request,"Your email is already verified")
            else:
                EmailAddrVerify.send_verification_email(request, user)
                messages.success(request,"Verification email sent successfully.")
        except User.DoesNotExist:
            messages.error(request,"No accounts found with this email")
        return redirect("accounts:login")


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
