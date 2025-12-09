from django.urls import path
from .views import ApplyLoanView, UploadDocumentsView, ApplicationDetailView

app_name = 'loans'

urlpatterns = [
    path('apply_loan',ApplyLoanView.as_view(), name='apply_loan'),
     path('application/<int:pk>/', ApplicationDetailView.as_view(), name='application_detail'),
    path('application/<int:pk>/documents/', UploadDocumentsView.as_view(), name='upload_documents'),
]
