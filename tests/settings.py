import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "tests",
    "management_auth",
]

SECRET_KEY = "abcde12345"

ROOT_URLCONF = "tests.urls"
