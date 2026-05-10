from django.urls import path
from .views import KYCVerificationView, KYCResultView

app_name="kyc"

urlpatterns = [
    path('kycselfverify/', KYCVerificationView.as_view(), name='kyc_verify'),
    path("result/",KYCResultView.as_view(),name="kyc_result" ),
]