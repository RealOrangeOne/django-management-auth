from django.contrib.auth import get_user_model
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

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])

        token = self.generator.make_token(user.id, options["timeout"])

        self.stdout.writelines([reverse("management_auth_login_as", args=[token])])
