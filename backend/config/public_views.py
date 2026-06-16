from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.membership.services.configuracao_service import ConfiguracaoService


class ConfigPublicaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "inscricoes_abertas": ConfiguracaoService.inscricoes_abertas(),
            }
        )
