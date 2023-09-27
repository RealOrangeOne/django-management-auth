from django.contrib.auth.views import redirect_to_login
from django.views import View


class LoginAsView(View):
    def get(self, request, token):
        return redirect_to_login("")
