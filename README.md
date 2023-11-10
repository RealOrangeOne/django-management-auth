# Django management auth

![CI](https://github.com/RealOrangeOne/django-management-auth/workflows/CI/badge.svg)
![PyPI](https://img.shields.io/pypi/v/django-management-auth.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-management-auth.svg)
![PyPI - License](https://img.shields.io/pypi/l/django-management-auth.svg)

Login to a Django application from a management command.

## Installation

```
pip install django-management-auth
```

Then, add `management_auth` to `INSTALLED_APPS`.

Finally, add the required URLs:

```python
# urls.py

urlpatterns += [path(".login-as", include("management_auth.urls"))]
```

## Usage

Authentication happens using a short-lived signed URL, generated from a management command.

```
./manage.py login_as <username>
```

This will create a URL for `<username>`. By default, the URLs are valid for 60 seconds (configurable with `--timeout`).

### Fully-qualified URLs

Where possible, URLs, are displayed fully-qualified, such that they can be quickly clicked to log in.

- To specify manually, use `MANAGEMENT_AUTH_BASE_URL`
- For Wagtail users, `WAGTAILADMIN_BASE_URL` is used to create the URL.
- For `django.contrib.sites` users, `SITE_ID` is correctly considered

If no base URL is found, a relative path is shown.

## Design considerations

- Tokens are only valid for a short amount of time, intended to prevent reuse / sharing.
- Tokens are signed URLs, rather than requiring a database table. This means the validation view is faster and more lightweight, and a database leak doesn't risk exposing sessions.
- Because tokens are signed, they can be used multiple times (however this is a bad idea)
