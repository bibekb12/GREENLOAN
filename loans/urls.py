from django.urls import path
from .views import (
    ApplyLoanView,
    BulkRepaymentPayView,
    RepaymentConfirmView,
    RepaymentListView,
    UploadDocumentsView,
    ApplicationDetailView,
    DocumentApproveReject,
    ApplicationStatusUpdateView,
    LandingPageView,
)

app_name = "loans"

urlpatterns = [
    path("landing",LandingPageView.as_view(), name="landing"),
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
    path("repayments/", RepaymentListView.as_view(), name="repayment_list"),
    path("repayments/confirm", RepaymentConfirmView.as_view(), name="repayment-confirm"),
    path("repayment/bulk-pay/", BulkRepaymentPayView.as_view(),name="bulk-repay",),

]
