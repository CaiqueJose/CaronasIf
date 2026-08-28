import time

from django.conf import settings
from django.contrib.auth import logout


class InactivityLogoutMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            agora = time.time()
            ultima_atividade = request.session.get("ultima_atividade")

            if ultima_atividade:

                tempo_inativo = agora - ultima_atividade

                if tempo_inativo >= settings.SESSION_COOKIE_AGE:
                    logout(request)

            if (
                request.user.is_authenticated
                and request.path != "/verificar-sessao/"
            ):
                request.session["ultima_atividade"] = agora

        response = self.get_response(request)

        return response