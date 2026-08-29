from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("verify-email/resend/", views.resend_email_view, name="resend_email"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", views.password_reset_request_view, name="password_reset_request"),
    path(
        "password-reset/<str:token>/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
]
