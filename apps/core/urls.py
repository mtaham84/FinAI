from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("about/", views.about_view, name="about"),
    path("services/", views.services_view, name="services"),
    path("support/", views.support_view, name="support"),
    path("contact/", views.contact_view, name="contact"),
    path("coming-soon/<str:section>/", views.coming_soon_view, name="coming_soon"),
]
