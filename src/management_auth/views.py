from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import redirect_to_login
from django.http.response import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from .tokens import ManagementAuthTokenGenerator

User = get_user_model()


@method_decorator(never_cache, name="dispatch")
class LoginAsView(View):
    token_generator = ManagementAuthTokenGenerator()

    head = View.http_method_not_allowed

    def get_success_url(self):
        return resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_error_response(self):
        return redirect_to_login("")

    def get(self, request, token):
        user_id = self.token_generator.get_user_from_token(token)

        if user_id is None:
            return self.get_error_response()

        user = User.objects.filter(id=user_id).first()

        if user is None:
            return self.get_error_response()

        user_last_login = user.last_login

        login(request, user)

        user.last_login = user_last_login
        user.save(update_fields=["last_login"])

        return HttpResponseRedirect(self.get_success_url())
