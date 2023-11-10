import string
from datetime import datetime
from io import StringIO

import time_machine
from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import NoReverseMatch, reverse
from django.utils.http import int_to_base36
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase
from management_auth.tokens import ManagementAuthTokenGenerator

token_strategy = st.text(
    alphabet=st.characters(
        codec="ascii", exclude_characters={"?", "#", *string.whitespace}
    ),
    min_size=3,
)


class LoginAsViewTestCase(HypothesisTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user-1")

        cls.generator = ManagementAuthTokenGenerator()

    def assertLoginSuccess(self, response):  # noqa:N802
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/profile/")
        self.assertTrue(get_user(self.client).is_authenticated)

    def assertLoginFail(self, response):  # noqa:N802
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=")
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_authenticates_user(self):
        token = self.generator.make_token(self.user.id)

        last_login = self.user.last_login

        with self.assertNumQueries(10):
            response = self.client.get(
                reverse("management_auth_login_as", args=[token])
            )

        self.user.refresh_from_db()

        self.assertLoginSuccess(response)
        self.assertEqual(get_user(self.client), self.user)
        self.assertEqual(self.user.last_login, last_login)

    def test_disallow_head_request(self):
        with self.assertNumQueries(0):
            response = self.client.head(
                reverse("management_auth_login_as", args=["not-a-token"])
            )

        self.assertEqual(response.status_code, 405)

    @given(token_strategy)
    def test_invalid_token(self, token):
        # Work around the reverse potentially failing
        url = reverse("management_auth_login_as", args=["token-placeholder"]).replace(
            "token-placeholder", token
        )

        with self.assertNumQueries(0):
            response = self.client.get(url)

        if response.status_code == 404:
            # If it was a 404, ensure it's because of URL resolving
            with self.assertRaises(NoReverseMatch):
                reverse("management_auth_login_as", args=[token])
        else:
            self.assertLoginFail(response)

    def test_authenticates_logged_in_user(self):
        user_2 = User.objects.create(username="user-2")
        self.client.force_login(user_2)
        self.assertEqual(get_user(self.client), user_2)

        token = self.generator.make_token(self.user.id)

        with self.assertNumQueries(10):
            response = self.client.get(
                reverse("management_auth_login_as", args=[token])
            )

        self.assertLoginSuccess(response)
        self.assertEqual(get_user(self.client), self.user)

    def test_no_cache(self):
        token = self.generator.make_token(self.user.id)
        response = self.client.get(reverse("management_auth_login_as", args=[token]))

        self.assertEqual(
            response["Cache-Control"],
            "max-age=0, no-cache, no-store, must-revalidate, private",
        )


@time_machine.travel(datetime(2023, 1, 1))
class TokenGeneratorTestCase(SimpleTestCase):
    def setUp(self):
        self.user = User(pk=1)
        self.user_2 = User(pk=2)

        self.generator = ManagementAuthTokenGenerator()

    def test_creates_token(self):
        self.assertEqual(
            self.generator.make_token(self.user.id),
            "1o-WzEsNjBd:1pBllg:6iGF6Rjv0I24e3Y0y-G_pXSaNg8UzExOHfeHglQ2UCo",
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

    @given(token_strategy)
    def test_invalid_token(self, token):
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


class LoginAsManagementCommandTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user-1")

    @time_machine.travel(datetime(2023, 1, 1))
    def test_creates_token(self):
        token = ManagementAuthTokenGenerator().make_token(self.user.id)

        stdout = StringIO()
        call_command("login_as", self.user.username, stdout=stdout)

        self.assertIn(token, stdout.getvalue())

        self.client.get(stdout.getvalue())
        self.assertEqual(get_user(self.client), self.user)

    @override_settings(MANAGEMENT_AUTH_BASE_URL="https://management-auth.com")
    def test_get_absolute_url(self):
        stdout = StringIO()
        call_command("login_as", self.user.username, stdout=stdout)

        self.assertIn("https://management-auth.com", stdout.getvalue())

    @override_settings(WAGTAILADMIN_BASE_URL="https://wagtail.org")
    def test_get_absolute_url_from_wagtail(self):
        stdout = StringIO()
        call_command("login_as", self.user.username, stdout=stdout)

        self.assertIn("https://wagtail.org", stdout.getvalue())

    @override_settings(SITE_ID=1)
    def test_get_absolute_url_from_django_site(self):
        stdout = StringIO()
        call_command("login_as", self.user.username, stdout=stdout)

        self.assertIn("https://example.com", stdout.getvalue())
