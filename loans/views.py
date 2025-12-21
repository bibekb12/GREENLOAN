from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from loans.forms import ApplicationForm, DocumentUploadForm
from loans.models import Application, Document
from django.contrib import messages


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
            or user.role in ["admin", "officer", "senior_officer"]
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
            "documents_verified": "documents_verified",
            "request_info": "info_requested",
            "info_provided": "info_provided",
            "salary_verified": "salary_verified",
            "proposal_approved": "proposal_approved",
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
        return redirect(request.META.get("HTTP_REFERER", reverse("accounts:dashboard")))
