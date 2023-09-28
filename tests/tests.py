from datetime import datetime

import time_machine
from django.contrib.auth.models import User
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils.http import int_to_base36
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

        self.generator = ManagementAuthTokenGenerator()

    def test_creates_token(self):
        self.assertEqual(
            self.generator.make_token(self.user.id),
            "a-WzEsMTBd:1pBllg:Q4adGs7nG1YBw44IJYJyGUE01TeayUU2biOdfEDj0tc",
        )

    def test_validates_token(self):
        token = self.generator.make_token(self.user.id)

        self.assertEqual(self.generator.get_user_from_token(token), self.user.id)

    def test_incorrect_timestamp(self):
        token = self.generator.make_token(self.user.id)

        timestamp, token = token.split(self.generator.timeout_sep, 1)

        timestamp = int_to_base36(15)

        self.assertIsNone(
            self.generator.get_user_from_token(
                self.generator.timeout_sep.join([timestamp, token])
            )
        )

    def test_no_token(self):
        self.assertIsNone(self.generator.get_user_from_token(""))

    def test_no_timestamp(self):
        token = self.generator.make_token(self.user.id)

        _, token = token.split(self.generator.timeout_sep, 1)

        self.assertIsNone(self.generator.get_user_from_token(token))

    def test_expired_token(self):
        token = self.generator.make_token(self.user.id)

        with time_machine.travel(datetime(2023, 1, 2)):
            self.assertIsNone(self.generator.get_user_from_token(token))

    def test_stable_tokens(self):
        self.assertEqual(
            self.generator.make_token(self.user.id),
            self.generator.make_token(self.user.id),
        )

    def test_different_tokens_for_different_users(self):
        self.assertNotEqual(
            self.generator.make_token(self.user.id),
            self.generator.make_token(self.user_2.id),
        )

    def test_different_token_for_different_timeout(self):
        self.assertNotEqual(
            self.generator.make_token(self.user.id),
            self.generator.make_token(self.user.id, timeout=15),
        )
