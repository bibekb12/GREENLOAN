from django.urls import path
from .views import (
    AdminUserCreateView,
    IndexView,
    ContactView,
    SystemSettingsListView,
    UserListView,
)

app_name = "core"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("settings/", SystemSettingsListView.as_view(), name="settings"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/create/", AdminUserCreateView.as_view(), name="user_create"),
]
