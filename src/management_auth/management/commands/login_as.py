from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.urls import reverse
from management_auth.tokens import ManagementAuthTokenGenerator

User = get_user_model()


class Command(BaseCommand):
    generator = ManagementAuthTokenGenerator()

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument(
            "--timeout", type=int, default=self.generator.default_timeout
        )

    def get_base_url(self):
        for setting in ["MANAGEMENT_AUTH_BASE_URL", "WAGTAILADMIN_BASE_URL"]:
            if base_url := getattr(settings, setting, None):
                return base_url

        if apps.is_installed("django.contrib.sites"):
            from django.contrib.sites.models import Site

            # Try Django's site framework
            try:
                return f"https://{Site.objects.get_current(None).domain}"
            except ImproperlyConfigured:
                pass

        return None

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])

        token = self.generator.make_token(user.id, options["timeout"])

        url = reverse("management_auth_login_as", args=[token])

        if base_url := self.get_base_url():
            url = base_url + url

        self.stdout.writelines([url])
