from datetime import datetime

import time_machine
from django.contrib.auth.models import User
from django.test import SimpleTestCase
from django.urls import reverse
from management_auth.tokens import ManagementAuthTokenGenerator


class LoginAsViewTestCase(SimpleTestCase):
    def test_accessible(self):
        response = self.client.get(reverse("management_auth_login_as", args=["foo"]))
        self.assertEqual(response.status_code, 302)


@time_machine.travel(datetime(2023, 1, 1))
class TokenGeneratorTestCase(SimpleTestCase):
    def setUp(self):
        self.user = User(pk=1)
        self.user_2 = User(pk=2)

    def test_creates_token(self):
        generator = ManagementAuthTokenGenerator()

        self.assertEqual(
            generator.make_token(self.user),
            "bhb600-20fa4482bb820a030482651c5de7b1df",
        )

    def test_stable_tokens(self):
        generator = ManagementAuthTokenGenerator()

        self.assertEqual(
            generator.make_token(self.user),
            generator.make_token(self.user),
        )

    def test_different_tokens_for_different_users(self):
        generator = ManagementAuthTokenGenerator()

        self.assertNotEqual(
            generator.make_token(self.user),
            generator.make_token(self.user_2),
        )
