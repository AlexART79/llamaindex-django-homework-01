from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:cv_id>/", views.details, name="details"),
    path("<int:cv_id>/summary/", views.summary, name="summary"),

]