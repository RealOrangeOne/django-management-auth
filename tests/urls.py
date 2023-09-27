from django.urls import include, path

urlpatterns = [path(".login-as", include("management_auth.urls"))]
