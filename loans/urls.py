from django.urls import path
from .views import ApplyLoanView

urlpatterns = [
    path('apply_loan',ApplyLoanView.as_view(), name='apply_loan'),
]
