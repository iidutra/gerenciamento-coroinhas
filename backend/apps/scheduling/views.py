from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communication.serializers import MensagemSerializer
from apps.identity.permissions import IsGestorCoroinhas, IsStaffPastoral
from apps.scheduling.models import Escala, EscalaMensal, Missa
from apps.scheduling.serializers import (
    AtribuirFuncoesSerializer,
    AtribuirGrupoCelebracaoSerializer,
    DefinirMembrosSerializer,
    EscalaMensalSerializer,
    EscalaSerializer,
    GerarEscalaMesSerializer,
    MissaSerializer,
    MontarEscalaSerializer,
    MoverCoroinhaCelebracaoSerializer,
    NotificarEscalaSerializer,
    RemanejarGrupoSerializer,
    TransferirCelebracaoSerializer,
)
from apps.scheduling.services.escala_service import EscalaService
from apps.scheduling.services.gerador_escala_mensal_service import GeradorEscalaMensalService
from apps.scheduling.services.notificacao_escala_service import NotificacaoEscalaService
from apps.scheduling.services.remanejamento_escala_service import RemanejamentoEscalaService
from apps.scheduling.services.relatorio_escala_service import RelatorioEscalaService


class MissaViewSet(viewsets.ModelViewSet):
    queryset = Missa.objects.all()
    serializer_class = MissaSerializer
    permission_classes = [IsStaffPastoral]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffPastoral()]
        return [IsGestorCoroinhas()]


class EscalaViewSet(mixins.DestroyModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Escala.objects.select_related("missa").prefetch_related("itens__coroinha")
    serializer_class = EscalaSerializer
    permission_classes = [IsStaffPastoral]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffPastoral()]
        return [IsGestorCoroinhas()]

    @action(detail=True, methods=["patch"], url_path="membros", permission_classes=[IsGestorCoroinhas])
    def membros(self, request, pk=None):
        escala = self.get_object()
        serializer = DefinirMembrosSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            EscalaService.definir_membros(escala, serializer.validated_data["coroinha_ids"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        escala = Escala.objects.prefetch_related("itens__coroinha").get(pk=escala.pk)
        return Response(EscalaSerializer(escala, context={"request": request}).data)

    @action(
        detail=True,
        methods=["patch"],
        url_path="mover-coroinha",
        permission_classes=[IsGestorCoroinhas],
    )
    def mover_coroinha(self, request, pk=None):
        escala = self.get_object()
        serializer = MoverCoroinhaCelebracaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            origem, destino = RemanejamentoEscalaService.mover_celebracao(
                coroinha_id=data["coroinha_id"],
                escala_origem_id=escala.pk,
                escala_destino_id=data.get("escala_destino_id"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        payload = {
            "origem": EscalaSerializer(origem, context={"request": request}).data,
        }
        if destino:
            payload["destino"] = EscalaSerializer(destino, context={"request": request}).data
        return Response(payload)

    @action(
        detail=True,
        methods=["patch"],
        url_path="atribuir-grupo",
        permission_classes=[IsGestorCoroinhas],
    )
    def atribuir_grupo(self, request, pk=None):
        escala = self.get_object()
        serializer = AtribuirGrupoCelebracaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            escala = RemanejamentoEscalaService.atribuir_grupo_celebracao(
                escala.pk,
                serializer.validated_data["grupo_numero"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        escala = Escala.objects.prefetch_related("itens__coroinha").get(pk=escala.pk)
        return Response(EscalaSerializer(escala, context={"request": request}).data)

    @action(detail=False, methods=["get", "delete"], url_path="mensal", permission_classes=[IsStaffPastoral])
    def mensal(self, request):
        try:
            ano = int(request.query_params.get("ano", timezone.now().year))
            mes = int(request.query_params.get("mes", timezone.now().month))
        except (TypeError, ValueError):
            return Response({"detail": "Ano e mês inválidos."}, status=status.HTTP_400_BAD_REQUEST)
        if not (1 <= mes <= 12):
            return Response({"detail": "Mês deve ser entre 1 e 12."}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == "DELETE":
            if not IsGestorCoroinhas().has_permission(request, self):
                return Response(status=status.HTTP_403_FORBIDDEN)
            escala_mensal = EscalaMensal.objects.filter(ano=ano, mes=mes).first()
            if not escala_mensal:
                return Response({"detail": "Escala mensal não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            escala_mensal.escalas.all().delete()
            escala_mensal.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        escala_mensal = (
            EscalaMensal.objects.filter(ano=ano, mes=mes)
            .prefetch_related("grupos__membros__coroinha")
            .first()
        )
        if not escala_mensal:
            return Response({"detail": "Escala mensal não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EscalaMensalSerializer(escala_mensal).data)

    @action(
        detail=False,
        methods=["patch"],
        url_path="mensal/remanejar-grupo",
        permission_classes=[IsGestorCoroinhas],
    )
    def remanejar_grupo(self, request):
        serializer = RemanejarGrupoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        escala_mensal = EscalaMensal.objects.filter(ano=data["ano"], mes=data["mes"]).first()
        if not escala_mensal:
            return Response({"detail": "Escala mensal não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        try:
            RemanejamentoEscalaService.mover_grupo(
                escala_mensal,
                data["coroinha_id"],
                data["grupo_destino"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        escala_mensal = (
            EscalaMensal.objects.filter(pk=escala_mensal.pk)
            .prefetch_related("grupos__membros__coroinha")
            .first()
        )
        escalas = Escala.objects.filter(escala_mensal=escala_mensal).prefetch_related("itens__coroinha")
        return Response(
            {
                "escala_mensal": EscalaMensalSerializer(escala_mensal).data,
                "escalas": EscalaSerializer(escalas, many=True, context={"request": request}).data,
            }
        )

    @action(
        detail=False,
        methods=["patch"],
        url_path="mensal/transferir-celebracao",
        permission_classes=[IsGestorCoroinhas],
    )
    def transferir_celebracao(self, request):
        serializer = TransferirCelebracaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        escala_mensal = EscalaMensal.objects.filter(ano=data["ano"], mes=data["mes"]).first()
        if not escala_mensal:
            return Response({"detail": "Escala mensal não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        try:
            origem, destino = RemanejamentoEscalaService.transferir_para_celebracao(
                escala_mensal,
                data["coroinha_id"],
                data["escala_destino_id"],
                grupo_numero=data.get("grupo_numero"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "origem": EscalaSerializer(origem, context={"request": request}).data,
                "destino": EscalaSerializer(destino, context={"request": request}).data,
            }
        )

    @action(detail=False, methods=["post"], url_path="gerar-mes", permission_classes=[IsGestorCoroinhas])
    def gerar_mes(self, request):
        serializer = GerarEscalaMesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            escala_mensal = GeradorEscalaMensalService.gerar(
                ano=data["ano"],
                mes=data["mes"],
                usuario=request.user,
                tamanho_grupo=data["tamanho_grupo"],
                quantidade_sexta=data["quantidade_sexta"],
                quantidade_comunidade=data["quantidade_comunidade"],
                substituir=data["substituir"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        escala_mensal = (
            EscalaMensal.objects.prefetch_related("grupos__membros__coroinha")
            .get(pk=escala_mensal.pk)
        )
        return Response(
            EscalaMensalSerializer(escala_mensal).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], permission_classes=[IsGestorCoroinhas])
    def montar(self, request):
        serializer = MontarEscalaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            escala, mensagem = EscalaService.montar_com_notificacao(
                data=data["data"],
                missa_id=data["missa_id"],
                modo=data["modo"],
                quantidade=data["quantidade"],
                usuario=request.user,
                coroinha_ids=data.get("coroinha_ids"),
                funcoes=data.get("funcoes"),
                notificar=data.get("notificar"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        escala = Escala.objects.prefetch_related("itens__coroinha").get(pk=escala.pk)
        payload = EscalaSerializer(escala, context={"request": request}).data
        if mensagem:
            payload["notificacao"] = MensagemSerializer(mensagem).data
        return Response(payload, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsGestorCoroinhas])
    def notificar(self, request, pk=None):
        escala = self.get_object()
        serializer = NotificarEscalaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            mensagem = NotificacaoEscalaService.notificar(
                escala,
                request.user,
                canal=serializer.validated_data.get("canal"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not mensagem:
            return Response({"detail": "Nenhum coroinha na escala."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MensagemSerializer(mensagem).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="funcoes", permission_classes=[IsGestorCoroinhas])
    def atribuir_funcoes(self, request, pk=None):
        escala = self.get_object()
        serializer = AtribuirFuncoesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            EscalaService.atribuir_funcoes(escala, serializer.validated_data.get("funcoes", {}))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        escala = Escala.objects.prefetch_related("itens__coroinha").get(pk=escala.pk)
        return Response(EscalaSerializer(escala, context={"request": request}).data)


class RelatorioEscalaMesView(APIView):
    permission_classes = [IsGestorCoroinhas]

    def get(self, request):
        hoje = timezone.now().date()
        try:
            mes = int(request.query_params.get("mes", hoje.month))
            ano = int(request.query_params.get("ano", hoje.year))
        except (TypeError, ValueError):
            return Response({"detail": "Mês e ano inválidos."}, status=status.HTTP_400_BAD_REQUEST)

        if not (1 <= mes <= 12):
            return Response({"detail": "Mês deve ser entre 1 e 12."}, status=status.HTTP_400_BAD_REQUEST)

        formato = request.query_params.get("formato", "pdf")
        if formato == "json":
            return Response(RelatorioEscalaService.exportar_mes_json(ano, mes))

        if formato == "csv":
            csv_content = RelatorioEscalaService.exportar_mes_csv(ano, mes)
            response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="escala-{ano}-{mes:02d}.csv"'
            return response

        pdf_bytes = RelatorioEscalaService.exportar_mes_pdf(ano, mes)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="escala-{ano}-{mes:02d}.pdf"'
        return response
