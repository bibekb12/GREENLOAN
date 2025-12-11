import os
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView
from loans.forms import ApplicationForm, DocumentUploadForm
from loans.models import Application, Document
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


# Create your views here.
class ApplyLoanView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = "loans/apply_loan.html"

    def test_func(self):
        return self.request.user.role == "customer"

    def handle_no_permission(self):
        messages.error(self.request, "Only customer can apply for loan.")
        return redirect("accounts:dashboard")

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
            or user.role == "admin"
        )

    def handle_no_permission(self):
        messages.error(
            self.request, "You dont have permission to view this application"
        )
        return redirect("accounts:dashboard")


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
        file_path = os.path.join("documents", file_name)

        saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
        form.instance.file_url = default_storage.url(saved_path)
        form.instance.file_name = uploaded_file.name
        form.instance.file_size = uploaded_file.size

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
