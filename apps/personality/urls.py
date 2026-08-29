from django.urls import path

from . import views

app_name = "personality"

urlpatterns = [
    path("", views.personality_home_view, name="index"),
]
