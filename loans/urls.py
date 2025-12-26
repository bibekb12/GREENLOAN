from django.urls import path
from .views import (
    ApplyLoanView,
    RepaymentListView,
    RepaymentPayView,
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
    path("repayments/pay/<int:pk>/", RepaymentPayView.as_view(), name="repay"),
]
