from django.urls import path
from . import views


urlpatterns = [
    path("", views.week_history, name="week-history"),
]
