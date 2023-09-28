from django.core.signing import BadSignature, TimestampSigner
from django.utils.http import base36_to_int, int_to_base36


class ManagementAuthTokenGenerator:
    key_salt = __name__
    timeout_sep = "-"

    def __init__(self):
        self.signer = TimestampSigner(salt=self.key_salt)

    def make_token(self, user_id, timeout=10):
        return (
            int_to_base36(timeout)
            + self.timeout_sep
            + self.signer.sign_object([user_id, timeout], compress=True)
        )

    def get_user_from_token(self, token):
        if not token:
            return None

        # Parse the token
        try:
            ts_b36, token = token.split(self.timeout_sep, 1)
        except ValueError:
            return None

        try:
            max_age = base36_to_int(ts_b36)
        except ValueError:
            return None

        try:
            user_id, timeout = self.signer.unsign_object(token, max_age=max_age)
        except BadSignature:
            return None

        if max_age != timeout:
            return None

        return user_id
