from django.urls import path
from accounts import views

app_name = "accounts"


urlpatterns = [
    path("password/change/", views.ChangePasswordView.as_view(), name="changepassword"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("kyc/", views.KYCListView.as_view(), name="kycapplication"),
    path("kyc/verify/<int:pk>/", views.VerifyKYCView.as_view(), name="verify_kyc"),
]
