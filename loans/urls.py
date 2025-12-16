from django.urls import path
from .views import (
    ApplyLoanView,
    UploadDocumentsView,
    ApplicationDetailView,
    DocumentApproveReject,
    ApplicationStatusUpdateView,
)

app_name = "loans"

urlpatterns = [
    path("apply_loan", ApplyLoanView.as_view(), name="apply_loan"),
    path(
        "application/<int:pk>/",
        ApplicationDetailView.as_view(),
        name="application_detail",
    ),
    path(
        "application/<int:pk>/documents/",
        UploadDocumentsView.as_view(),
        name="upload_documents",
    ),
    path(
        "application/<int:pk>/documents/approvereject",
        DocumentApproveReject.as_view(),
        name="document_approve_reject",
    ),
    path(
        "application/<int:pk>/status-update/",
        ApplicationStatusUpdateView.as_view(),
        name="application_status_update",
    ),
]
