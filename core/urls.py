from django.urls import path
from core.views import (
    AdminListView,
    UserCreateView,
    AdminCreateView,
    IndexView,
    ContactView,
    SystemSettingsListView,
    UserListView,
    SitePageSettingsView,
)

app_name = "core"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("settings/", SystemSettingsListView.as_view(), name="settings"),
    path("settings/users/", UserListView.as_view(), name="user_list"),
    path("settings/admins/", AdminListView.as_view(), name="admin_list"),
    path("settings/users/create/", UserCreateView.as_view(), name="user_create"),
    path("settings/admin/create/", AdminCreateView.as_view(), name="admin_create"),
    path("settings/sitesetting", SitePageSettingsView.as_view(), name="site_settings"),
]
