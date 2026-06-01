from django.urls import path
from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path(
        "<int:project_pk>/rolls/<int:roll_pk>/",
        views.roll_detail,
        name="roll_detail",
    ),
    path("<int:pk>/", views.project_detail, name="project_detail"),
]
