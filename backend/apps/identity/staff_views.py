from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.identity.models import TipoPerfil
from apps.identity.permissions import IsCoordenador
from apps.identity.services.usuario_staff_service import UsuarioStaffService
from apps.identity.staff_serializers import (
    AtualizarUsuarioStaffSerializer,
    CriarUsuarioStaffSerializer,
    UsuarioStaffSerializer,
)


class UsuarioStaffViewSet(viewsets.ViewSet):
    permission_classes = [IsCoordenador]

    def list(self, request):
        qs = UsuarioStaffService.listar()
        return Response(UsuarioStaffSerializer(qs, many=True).data)

    def create(self, request):
        serializer = CriarUsuarioStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            usuario = UsuarioStaffService.criar(**serializer.validated_data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UsuarioStaffSerializer(usuario).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        usuario = UsuarioStaffService.listar().filter(pk=pk).first()
        if not usuario:
            return Response({"detail": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AtualizarUsuarioStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            usuario = UsuarioStaffService.atualizar(usuario, serializer.validated_data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UsuarioStaffSerializer(usuario).data)
