from django.urls import path

from . import views

urlpatterns = [
    path("/<token>/", views.LoginAsView.as_view(), name="management_auth_login_as")
]
