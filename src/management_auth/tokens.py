from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


class ManagementAuthTokenGenerator(PasswordResetTokenGenerator):
    key_salt = __name__

    def __init__(self, timeout=10):
        super().__init__()
        self.timeout = timeout

    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.

        A modified version from `PasswordResetTokenGenerator` which reads the
        timeout from the instance.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(user, ts, secret),
                token,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self._num_seconds(self._now()) - ts) > settings.PASSWORD_RESET_TIMEOUT:
            return False

        return True

    def _make_hash_value(self, user, timestamp):
        """
        Hash the user's primary key(if available).

        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        return f"{user.pk}{timestamp}"
