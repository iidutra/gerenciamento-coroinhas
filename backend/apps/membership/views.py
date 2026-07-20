import json

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.permissions import IsFamiliaOuStaff
from apps.identity.permissions import IsFamilia, IsGestorCoroinhas, IsStaffPastoral
from apps.membership.models import (
    Coroinha,
    Inscricao,
    SolicitacaoAcesso,
    StatusInscricao,
    StatusSolicitacao,
)
from apps.membership.serializers import (
    AniversarianteSerializer,
    CoroinhaResumoPortalSerializer,
    CoroinhaSerializer,
    CoroinhaVerificadaSerializer,
    InscricaoPublicaSerializer,
    InscricaoSerializer,
    SolicitacaoAcessoSerializer,
    SolicitarAcessoSerializer,
    VerificarAcessoSerializer,
)
from apps.membership.services.coroinha_service import CoroinhaService
from apps.membership.services.configuracao_service import ConfiguracaoService
from apps.membership.services.inscricao_service import InscricaoService
from apps.membership.services.portal_service import PortalService
from apps.membership.services.relatorio_service import RelatorioService
from apps.membership.services.solicitacao_acesso_service import SolicitacaoAcessoService


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class InscricaoPublicaView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        if request.content_type and "multipart" in request.content_type:
            raw = request.data.get("dados", "{}")
            try:
                payload = json.loads(raw) if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                return Response({"detail": "Dados inválidos."}, status=status.HTTP_400_BAD_REQUEST)
            foto = request.FILES.get("foto")
        else:
            payload = request.data
            foto = None

        serializer = InscricaoPublicaSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        try:
            inscricao = InscricaoService.criar_publica(
                serializer.validated_data,
                foto=foto,
                ip=_client_ip(request),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"id": inscricao.id, "status": inscricao.status, "detail": "Inscrição enviada com sucesso."},
            status=status.HTTP_201_CREATED,
        )


class InscricaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Inscricao.objects.all()
    serializer_class = InscricaoSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffPastoral()]
        return [IsGestorCoroinhas()]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=True, methods=["post"])
    def aprovar(self, request, pk=None):
        inscricao = self.get_object()
        mensagem = request.data.get("mensagem", "")
        notificar = request.data.get("notificar", True)
        if isinstance(notificar, str):
            notificar = notificar.lower() in ("true", "1", "yes")
        try:
            coroinha = InscricaoService.aprovar(
                inscricao,
                request.user,
                mensagem=mensagem or "",
                notificar=bool(notificar),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"coroinha_id": coroinha.id, "status": inscricao.status})

    @action(detail=True, methods=["post"])
    def rejeitar(self, request, pk=None):
        inscricao = self.get_object()
        mensagem = request.data.get("mensagem", "")
        notificar = request.data.get("notificar", True)
        if isinstance(notificar, str):
            notificar = notificar.lower() in ("true", "1", "yes")
        try:
            InscricaoService.rejeitar(
                inscricao,
                mensagem=mensagem or "",
                notificar=bool(notificar),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": StatusInscricao.REJEITADA})


class CoroinhaViewSet(viewsets.ModelViewSet):
    queryset = Coroinha.objects.all()
    serializer_class = CoroinhaSerializer
    permission_classes = [IsStaffPastoral]
    filterset_fields = ["status", "turma"]
    search_fields = ["nome"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffPastoral()]
        if self.action == "aniversariantes":
            return [IsFamiliaOuStaff()]
        return [IsGestorCoroinhas()]

    @action(detail=False, methods=["get"], url_path="aniversariantes")
    def aniversariantes(self, request):
        mes = request.query_params.get("mes")
        mes_int = int(mes) if mes else None
        qs = CoroinhaService.aniversariantes_do_mes(mes_int)
        return Response(AniversarianteSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="foto", parser_classes=[MultiPartParser, FormParser])
    def upload_foto(self, request, pk=None):
        coroinha = self.get_object()
        foto = request.FILES.get("foto")
        if not foto:
            return Response({"detail": "Envie o arquivo no campo 'foto'."}, status=status.HTTP_400_BAD_REQUEST)
        coroinha.foto = foto
        coroinha.save(update_fields=["foto"])
        return Response(CoroinhaSerializer(coroinha, context={"request": request}).data)


class PortalCoroinhaView(APIView):
    permission_classes = [IsFamiliaOuStaff]

    def get(self, request, coroinha_id):
        try:
            resumo = PortalService.get_resumo(request.user, coroinha_id, request=request)
        except PermissionError:
            return Response({"detail": "Sem permissão."}, status=status.HTTP_403_FORBIDDEN)
        except Coroinha.DoesNotExist:
            return Response({"detail": "Coroinha não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CoroinhaResumoPortalSerializer(resumo)
        return Response(serializer.data)


class PortalFilhosView(APIView):
    permission_classes = [IsFamiliaOuStaff]

    def get(self, request):
        coroinhas = PortalService.coroinhas_acessiveis(request.user)
        data = CoroinhaSerializer(coroinhas, many=True, context={"request": request}).data
        return Response(data)


class AcessoVerificarView(APIView):
    """Passo 1 do auto-acesso do pai: identifica o coroinha por nome + data nasc."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerificarAcessoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            coroinhas = SolicitacaoAcessoService.verificar(
                serializer.validated_data["nome"],
                serializer.validated_data["data_nascimento"],
                ip=_client_ip(request),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        data = CoroinhaVerificadaSerializer(coroinhas, many=True).data
        return Response({"coroinhas": data})


class AcessoSolicitarView(APIView):
    """Passo 2 do auto-acesso: CPF + senha; cria pedido pendente de aprovação."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SolicitarAcessoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data
        try:
            SolicitacaoAcessoService.solicitar(
                coroinha_id=v["coroinha_id"],
                nome_coroinha=v["nome"],
                data_nascimento=v["data_nascimento"],
                nome_responsavel=v["nome_responsavel"],
                cpf=v["cpf"],
                senha=v["senha"],
                whatsapp=v.get("whatsapp", ""),
                ip=_client_ip(request),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "detail": (
                    "Pedido enviado! Assim que a coordenação aprovar, "
                    "você poderá entrar com seu CPF e senha."
                )
            },
            status=status.HTTP_201_CREATED,
        )


class SolicitacaoAcessoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SolicitacaoAcesso.objects.select_related("coroinha").all()
    serializer_class = SolicitacaoAcessoSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "pendentes_count"):
            return [IsStaffPastoral()]
        return [IsGestorCoroinhas()]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=False, methods=["get"], url_path="pendentes-count")
    def pendentes_count(self, request):
        total = SolicitacaoAcesso.objects.filter(status=StatusSolicitacao.PENDENTE).count()
        return Response({"pendentes": total})

    @action(detail=True, methods=["post"])
    def aprovar(self, request, pk=None):
        solicitacao = self.get_object()
        try:
            usuario = SolicitacaoAcessoService.aprovar(solicitacao, request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": solicitacao.status, "usuario_id": usuario.id})

    @action(detail=True, methods=["post"])
    def rejeitar(self, request, pk=None):
        solicitacao = self.get_object()
        try:
            SolicitacaoAcessoService.rejeitar(solicitacao, request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": solicitacao.status})


class DashboardStatsView(APIView):
    permission_classes = [IsStaffPastoral]

    def get(self, request):
        total = Coroinha.objects.count()
        ativos = Coroinha.objects.filter(status="Ativo").count()
        em_formacao = Coroinha.objects.filter(status="EmFormacao").count()
        inscricoes_pendentes = Inscricao.objects.filter(status="Pendente").count()
        extra = RelatorioService.dashboard_stats_extra()
        return Response(
            {
                "total_coroinhas": total,
                "ativos": ativos,
                "em_formacao": em_formacao,
                "inscricoes_pendentes": inscricoes_pendentes,
                **extra,
            }
        )


class ProximasEscalasView(APIView):
    permission_classes = [IsStaffPastoral]

    def get(self, request):
        return Response(PortalService.proximas_escalas_dashboard())


class RelatorioGeralView(APIView):
    permission_classes = [IsStaffPastoral]

    def get(self, request):
        return Response(RelatorioService.relatorio_geral())


class ConfigInscricoesView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsStaffPastoral()]
        return [IsGestorCoroinhas()]

    def get(self, request):
        return Response(ConfiguracaoService.status_inscricoes())

    def patch(self, request):
        aberto = request.data.get("inscricoes_abertas")
        if not isinstance(aberto, bool):
            return Response(
                {"detail": "Informe inscricoes_abertas como true ou false."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        config = ConfiguracaoService.definir_inscricoes_abertas(aberto, request.user)
        return Response(
            {
                **ConfiguracaoService.status_inscricoes(),
                "detail": "Inscrições abertas." if aberto else "Inscrições fechadas.",
            }
        )
