from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View, TemplateView
from loans.forms import ApplicationForm, DocumentUploadForm
from loans.models import Application, ApprovedLoans, Document, Repayment
from django.contrib import messages
from django.utils import timezone
from loans.utils import create_repayments, update_credit_score
from loans.signals import loan_approved_signal
from datetime import date, datetime, timedelta
from calendar import monthrange
from django.db.models import Count, Sum, Q
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth import get_user_model
from calendar import month_name, monthrange

User = get_user_model()



# Create your views here.
class ApplyLoanView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = "loans/apply_loan.html"

    def test_func(self):
        user = self.request.user
        if user.role != "customer":
            return False

        # kyc check
        if user.kyc_status != "verified":
            return False

        return True

    def handle_no_permission(self):
        if self.request.user.role != "customer":
            messages.error(self.request, "Only customer can apply for loan.")
            return redirect("accounts:dashboard")

        if self.request.user.kyc_status != "verified":
            messages.error(self.request, "Kyc should be verified for loan apply.")
            return redirect("accounts:profile")

    def form_valid(self, form):
        form.instance.applicant = self.request.user
        application = form.save()
        application.add_status_history(
            "submitted", self.request.user, "Application submitted"
        )
        messages.success(self.request, "Application submitted succesfully")
        return redirect("loans:upload_documents", pk=application.pk)


class ApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Application
    template_name = "loans/application_detail.html"
    context_object_name = "application"

    def test_func(self):
        application = self.get_object()
        user = self.request.user
        return (
            user == application.applicant
            or user == application.officer
            or user.role in ["admin", "officer", "senior_officer","customer"]
        )

    def handle_no_permission(self):
        messages.error(
            self.request, "You dont have permission to view this application"
        )
        return redirect("accounts:dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_object()
        user = self.request.user

        context["documents"] = application.documents.all()

        context["can_upload_docs"] = (
            self.request.user == application.applicant
            and application.status in ["submitted", "info_requested"]
        )

        context["can_view_docs"] = (
            self.request.user == application.applicant
            or self.request.user == application.officer
            or self.request.user.role in ["customer", "officer", "senior_officer"]
        )

        # Applicant allowed actions
        applicant_actions = []
        if user == application.applicant:
            if application.status in ["info_requested"]:
                applicant_actions.append("upload_documents")

        # Officer allowed actions
        officer_actions = []
        if user.role in ["officer", "senior_officer"]:
            if application.status in ["submitted", "under_review"]:
                officer_actions.extend(["review", "request_info"])
            elif application.status == "info_provided":
                officer_actions.append("verify_documents")
            elif application.status == "documents_verified":
                officer_actions.append("verify_salary")
            elif application.status == "salary_verified":
                officer_actions.append("approve_proposal")
            elif application.status == "proposal_approved":
                officer_actions.append("final_review")
            elif application.status == "final_review":
                officer_actions.extend(["approve_application", "reject_application"])

        context["applicant_actions"] = applicant_actions
        context["officer_actions"] = officer_actions

        return context


class UploadDocumentsView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = "loans/upload_documents.html"

    def test_func(self):
        application = get_object_or_404(Application, pk=self.kwargs["pk"])
        return self.request.user == application.applicant

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to upload documents.")
        return redirect("accounts:dashboard")

    def get_context_data(self, **kwargs):
        """
        Provide the related application to the template so links like
        \"Back to application\" can resolve correctly.
        """
        context = super().get_context_data(**kwargs)
        context["application"] = get_object_or_404(Application, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        application = get_object_or_404(Application, pk=self.kwargs["pk"])
        form.instance.application = application

        # Handle file upload
        uploaded_file = self.request.FILES["file"]
        file_name = (
            f"{application.id}_{form.instance.document_type}_{uploaded_file.name}"
        )
        form.instance.file.save(file_name, uploaded_file)

        form.save()
        if application.status == "info_requested":
            application.status = "info_provided"
            application.add_status_history(
                "info_provided",
                self.request.user,
                "Applicant uploaded additional documents",
            )
            application.save(update_fields=["status"])

        messages.success(self.request, "Document uploaded successfully!")
        return redirect("loans:application_detail", pk=application.pk)


class DocumentApproveReject(LoginRequiredMixin, UserPassesTestMixin, View):
    """Here documents are approved or rejected by officer and senior officer"""

    def test_func(self):
        return self.request.user.role in ["officer", "senior_officer"]

    def handle_no_permission(self):
        messages.error(
            self.request, "You dont have permission to approve or reject documents."
        )
        return redirect("accounts:dashboard")

    def post(self, request, *args, **kwargs):
        document_id = request.POST.get("document_id")
        action = request.POST.get("action")

        document = get_object_or_404(Document, id=document_id)
        application = document.application

        if action not in ["approve", "reject"]:
            messages.error(request, "Invalid action.")
            return redirect("loans:application_detail", pk=application.pk)

        if action == "approve":
            document.verification_status = "verified"
            messages.success(
                request, f"Document '{document.document_type}' approved successfully."
            )
        else:
            document.verification_status = "rejected"
            messages.warning(request, f"Document '{document.document_type}' rejected.")

        document.save(update_fields=["verification_status"])

        if hasattr(application, "add_status_history"):
            application.add_status_history(
                status=document.verification_status,
                user=request.user,
                note=f"Document '{document}' {document.verification_status} by {request.user.username}",
            )
            application.save()

        return redirect("loans:application_detail", pk=application.pk)


class ApplicationStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Change the status of an application based on POST 'action'.
    Only accessible to officers and senior officers.
    """

    def test_func(self):
        return self.request.user.role in ["officer", "senior_officer"]

    def post(self, request, *args, **kwargs):
        application_id = kwargs.get("pk")
        application = get_object_or_404(Application, pk=application_id)
        action = request.POST.get("action")

        if not action:
            messages.error(request, "No action provided.")
            return redirect(
                request.META.get("HTTP_REFERER", reverse("accounts:dashboard"))
            )

        # Map actions to status
        status_map = {
            "approve": "approved",
            "reject": "rejected",
            "verify": "verified",
            "request_info": "info_requested",
            "info_provided": "info_provided",
            "final_review": "final_review",
        }

        new_status = status_map.get(action)
        if not new_status:
            messages.error(request, "Invalid action.")
            return redirect(
                request.META.get("HTTP_REFERER", reverse("accounts:dashboard"))
            )

        application.status = new_status
        application.save()
        messages.success(
            request,
            f"Application status changed to '{application.get_status_display()}'.",
        )
        if new_status == "approved":
            approved_loan = ApprovedLoans.objects.create(
                application=application,
                principle=application.amount,
                interest_rate=application.loan_type.interest_rate,
                tenure_months=application.duration_months,
                approved_by = self.request.user,
                status="active"
            )
            loan_approved_signal.send(
                sender=None,
                loan_type = application.loan_type.name,
                to_user = application.applicant
            )

            # generate repayments
            create_repayments(approved_loan)

        return redirect(request.META.get("HTTP_REFERER", reverse("accounts:dashboard")))
    

class RepaymentPayView(LoginRequiredMixin, UpdateView):
    model = Repayment
    template_name = "loans/repayment_confirm.html"
    fields = []  # no form fields
    success_url = reverse_lazy("loans:repayment_list")

    def get_queryset(self):
        # Security: user can pay only own repayments
        return Repayment.objects.filter(loan__application__applicant=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.now().date()
        return context

    def form_valid(self, form):
        repayment = form.instance
        today = timezone.now().date()

        repayment.amount_paid = repayment.amount_due
        repayment.paid_date = today

        if today > repayment.due_date:
            repayment.status = "late"
        else:
            repayment.status = "paid"

        repayment.save()

        # Update credit score
        update_credit_score(self.request.user, repayment)

        return super().form_valid(form)


class RepaymentListView(ListView):
    model = Repayment
    template_name = "loans/repayment_list.html"
    context_object_name = "repayments"

    def get_queryset(self):
        loan_id = self.request.GET.get("loan_id")
        
        # Get latest loan per application
        loans_qs = ApprovedLoans.objects.filter(application__applicant=self.request.user).order_by("-approved_at")
        latest_loans_dict = {}
        for loan in loans_qs:
            if loan.application_id not in latest_loans_dict:
                latest_loans_dict[loan.application_id] = loan
        loans = list(latest_loans_dict.values())

        self.selected_loan = None
        if loan_id:
            for loan in loans:
                if str(loan.id) == str(loan_id):
                    self.selected_loan = loan
                    break

        if self.selected_loan:
            repayments = self.selected_loan.repayments.annotate(
                status_order=Case(
                    When(status='pending', then=Value(0)),
                    When(status='late', then=Value(1)),
                    When(status='paid', then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField()
                )
            ).order_by('status_order', 'due_date')
        else:
            repayments = Repayment.objects.none()

        self.loans = loans
        return repayments


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["loans"] = getattr(self, "loans", [])
        context["selected_loan"] = getattr(self, "selected_loan", None)
        return context



class LandingPageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/landing.html"
    context_object_name = "staticdata"

    def test_func(self):
        return self.request.user.role != "customer"

    def handle_no_permission(self):
        return redirect("accounts:dashboard")

    # -----------------------
    # DATE RANGE HANDLER
    # -----------------------
    def get_date_range(self):
        today = date.today()
        range_type = self.request.GET.get("range", "month")

        if range_type == "today":
            start = end = today

        elif range_type == "custom":
            try:
                start = datetime.strptime(
                    self.request.GET.get("start"), "%Y-%m-%d"
                ).date()
                end = datetime.strptime(
                    self.request.GET.get("end"), "%Y-%m-%d"
                ).date()
            except Exception:
                start = today.replace(day=1)
                end = today

        else:  # this month (default)
            start = today.replace(day=1)
            end = today.replace(day=monthrange(today.year, today.month)[1])

        return start, end, range_type

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        start_date, end_date, range_type = self.get_date_range()

        # ---------------- KPI ----------------
        total_users = User.objects.exclude(role="customer").count()

        total_applications = Application.objects.filter(
            created_at__date__range=(start_date, end_date)
        ).count()

        approved_loans = ApprovedLoans.objects.filter(
            approved_at__range=(start_date, end_date),
            status="active"
        ).count()

        total_revenue = (
            Repayment.objects.filter(
                status="paid",
                paid_date__range=(start_date, end_date)
            )
            .aggregate(total=Sum("amount_paid"))
            .get("total") or 0
        )

        # ---------------- Application Status ----------------
        application_qs = (
            Application.objects
            .filter(created_at__date__range=(start_date, end_date))
            .order_by()
            .values("status")
            .annotate(count=Count("id"))
        )

        status_map = {
            "submitted": ("Submitted", "primary"),
            "under_review": ("Under Review", "warning"),
            "approved": ("Approved", "success"),
            "rejected": ("Rejected", "danger"),
        }

        application_status = [
            {
                "label": status_map[row["status"]][0],
                "count": row["count"],
                "color": status_map[row["status"]][1],
            }
            for row in application_qs
            if row["status"] in status_map
        ]

        # ---------------- KYC ----------------
        kyc_qs = (
            User.objects
            .order_by()
            .values("kyc_status")
            .annotate(count=Count("id"))
        )

        kyc = {"pending": 0, "verified": 0, "rejected": 0}
        for row in kyc_qs:
            if row["kyc_status"] in kyc:
                kyc[row["kyc_status"]] = row["count"]

        # ---------------- Loan Health ----------------
        loan_qs = (
            ApprovedLoans.objects
            .filter(approved_at__range=(start_date, end_date))
            .order_by()
            .values("status")
            .annotate(count=Count("id"))
        )

        loan_map = {
            "active": "Active Loans",
            "closed": "Closed Loans",
            "defaulted": "Defaulted Loans",
        }

        loan_health = [
            {"title": loan_map[row["status"]], "value": row["count"]}
            for row in loan_qs
            if row["status"] in loan_map
        ]
        # ---------------- Revenue Trend ----------------
        revenue_trend = []
        current_day = start_date
        while current_day <= end_date:
            day_total = Repayment.objects.filter(
                status="paid",
                paid_date=current_day
            ).aggregate(total=Sum("amount_paid")).get("total") or 0
            revenue_trend.append({
                "date": current_day.strftime("%Y-%m-%d"),
                "amount": day_total
            })
            current_day += timedelta(days=1)
        # ---------------- Context ----------------
        context["staticdata"] = {
            "total_users": total_users,
            "total_applications": total_applications,
            "approved_loans": approved_loans,
            "total_revenue": round(total_revenue, 2),
            "application_status": application_status,
            "kyc": kyc,
            "loan_health": loan_health,
            "revenue_trend": revenue_trend
        }

        context["filters"] = {
            "range": range_type,
            "start": start_date,
            "end": end_date,
        }

        return context
