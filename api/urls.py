from django.urls import path
from .views_auth import admin_login, student_login, get_current_user_profile, unified_login, student_signup
from .views_internship import get_programs, get_domains, get_public_settings, register_application, get_application_status
from .views_admin import (
    get_dashboard_stats,
    get_all_applications,
    get_application_detail,
    update_application_status,
    delete_application,
    export_applications_csv,
    admin_settings_view
)
from .views_student import get_student_application, update_student_profile

urlpatterns = [
    # Auth
    path("auth/login/", unified_login, name="unified-login"),
    path("auth/signup/", student_signup, name="student-signup"),
    path("auth/admin-login/", admin_login, name="admin-login"),
    path("auth/student-login/", student_login, name="student-login"),
    path("auth/me/", get_current_user_profile, name="auth-me"),

    # Public Internship Endpoints
    path("programs/", get_programs, name="get-programs"),
    path("domains/", get_domains, name="get-domains"),
    path("settings/public/", get_public_settings, name="public-settings"),
    path("register/", register_application, name="register-application"),
    path("application/<str:application_id>/", get_application_status, name="application-status"),

    # SuperAdmin Endpoints
    path("admin/dashboard-stats/", get_dashboard_stats, name="admin-stats"),
    path("admin/applications/", get_all_applications, name="admin-applications"),
    path("admin/applications/<str:application_id>/", get_application_detail, name="admin-app-detail"),
    path("admin/applications/<str:application_id>/status/", update_application_status, name="admin-app-status"),
    path("admin/applications/<str:application_id>/delete/", delete_application, name="admin-app-delete"),
    path("admin/export-csv/", export_applications_csv, name="admin-export-csv"),
    path("admin/settings/", admin_settings_view, name="admin-settings"),

    # Student Portal Endpoints
    path("student/my-application/", get_student_application, name="student-application"),
    path("student/update-profile/", update_student_profile, name="student-update-profile"),
]
