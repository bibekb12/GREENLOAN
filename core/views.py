import json
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect
from django.core.mail import send_mail
from accounts.forms import SimpleUserCreationForm
from core.models import SitePage
from core.forms import SimpleAdminCreationForm
from greenloan import settings
from loans.models import LoanTypes, Document

User = get_user_model()


class IndexView(TemplateView):
    """This views return the index page for the application"""

    model = SitePage
    # context_name = "LoanTypes"
    template_name = "core/index.html"

    # def get(self, request, *args, **kwargs):
    #     return LoanTypes.objects.filter(is_active = True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["LoanTypes"] = LoanTypes.objects.filter(is_active = True)
        context["loan_detail"] = ['Loan Amount', 'Repayment Period', 'Interest Rate', 'Application Fee']
        context["features"] = ['Secure', 'Fast', 'Low Interest', 'Trusted']
        return context


class ContactView(TemplateView):
    template_name = "core/contact.html"

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Construct the message for admin
        admin_subject = f"New Contact Form Submission: {subject}"
        admin_message = f"""
        Name: {name}
        Email: {email}
        Subject: {subject}
        Message:
        {message}
        """

        # Send email to company/admin
        send_mail(
            subject=admin_subject,
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # your company email
            fail_silently=False,
        )

        # Optional: Send confirmation email to sender
        sender_subject = "Thank you for contacting GreenLoan"
        sender_message = f"Hi {name},\n\nThank you for reaching out. We received your message and will respond soon.\n\nYour message:\n{message}\n\nBest regards,\nGreenLoan Team"

        send_mail(
            subject=sender_subject,
            message=sender_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect('core:contact')  # replace with your url name


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
        queryset = User.objects.filter(role="customer")
        role = self.request.GET.get("role")
        if role:
            queryset = queryset.filter(role=role)
        return queryset


class AdminListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "core/admin_list.html"
    context_object_name = "admin"
    paginate_by = 10

    def test_func(self):
        return self.request.user.role == "admin"

    def get_queryset(self):
        queryset = User.objects.exclude(role="customer")
        role = self.request.GET.get("role")
        if role:
            queryset = queryset.filter(role=role)
        return queryset


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
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
        return redirect("core:user_list")


class AdminCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = SimpleAdminCreationForm
    template_name = "core/admin_create.html"

    def test_func(self):
        return self.request.user.role == "admin"

    def handle_no_permission(self):
        messages.error(self.request, "You dont have permission.")
        return redirect("accounts:dashboard")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = self.request.POST.get("role")
        user.phone = self.request.POST.get("phone", "")
        user.save()

        messages.success(
            self.request,
            f"User {user.get_full_name() or user.username} created successfully.",
        )
        return redirect("core:admin_list")


class SitePageSettingsView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SitePage
    fields = "__all__"
    template_name = "core/site_setting.html"
    context_object_name = "sitesettings"

    def get_queryset(self):
        return SitePage.objects.first()

    def test_func(self):
        return self.request.user.role == "admin"

    def handle_no_permission(self):
        messages.error(self.request, "You dont have permission to settings site.")
        return redirect("core:dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allowed_precent"] = SitePage.objects.first()
        loan_types = LoanTypes.objects.all()
        for loan in loan_types:
            loan.documents_json = json.dumps(loan.required_documents)
        context["loan_types"] = loan_types
        context["document_choices"] = Document.DOCUMENT_TYPES
        return context
    
    def post(self, request, *args, **kwargs):

        if "loan_types_save" in request.POST and "interest_rate" in request.POST:
            loan_id = request.POST.get("loan_id")
            name = request.POST.get("name").strip()
            docs = request.POST.getlist("required_documents")

            # 🔒 unique name check (exclude self on update)
            qs = LoanTypes.objects.filter(name__iexact=name)
            if loan_id:
                qs = qs.exclude(id=loan_id)

            if qs.exists():
                messages.error(request, "Loan Type with this name already exists.")
                return redirect("core:site_settings")

            # 🎯 CORE LOGIC
            if loan_id:
                # UPDATE
                loan = LoanTypes.objects.get(id=loan_id)
                msg = "Loan Type updated successfully"
            else:
                # INSERT
                loan = LoanTypes()
                msg = "Loan Type created successfully"

            loan.name = name
            loan.interest_rate = request.POST.get("interest_rate")
            loan.amount_limit = request.POST.get("amount_limit")
            loan.is_active = request.POST.get("is_active") == "true"
            loan.description = request.POST.get("description")
            loan.required_documents = docs

            loan.full_clean()
            loan.save()

            messages.success(request, msg)
            return redirect("core:site_settings")
        
        if "allowed_percent_save" in request.POST:
            allowed = request.POST.get("allowed_percent")

            site = SitePage.objects.first()
            if not site:
                site = SitePage()

            site.allowed_income_percent = allowed
            site.save()

            messages.success(request, "Allowed income percent saved successfully.")
            return redirect("core:site_settings")


        return super().post(request, *args, **kwargs)
