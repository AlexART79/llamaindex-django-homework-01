from django.urls import path

from . import views

urlpatterns = [
    path("", views.cv_index, name="index"),
    path("<int:cv_id>/", views.cv_details, name="details"),
    path("<int:cv_id>/summary/", views.cv_summary, name="summary"),
]