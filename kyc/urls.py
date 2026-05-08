from django.urls import path
from .views import KYCVerificationView

urlpatterns = [
    path('kycselfverify/', KYCVerificationView.as_view(), name='kyc_verify'),
]