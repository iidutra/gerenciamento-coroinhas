from django.db import transaction

from apps.identity.models import TipoPerfil, Usuario

STAFF_PERFIS = (TipoPerfil.COORDENADOR, TipoPerfil.SECRETARIO, TipoPerfil.PADRE)


class UsuarioStaffService:
    @staticmethod
    def listar():
        return Usuario.objects.filter(tipo_perfil__in=STAFF_PERFIS).order_by("nome")

    @staticmethod
    @transaction.atomic
    def criar(nome: str, email: str, tipo_perfil: str, senha: str) -> Usuario:
        if tipo_perfil not in (TipoPerfil.SECRETARIO, TipoPerfil.PADRE):
            raise ValueError("Só é possível criar Secretário ou Padre.")
        return Usuario.objects.create_user(
            email=email.lower(),
            nome=nome,
            tipo_perfil=tipo_perfil,
            password=senha,
        )

    @staticmethod
    @transaction.atomic
    def atualizar(usuario: Usuario, dados: dict) -> Usuario:
        if usuario.tipo_perfil == TipoPerfil.COORDENADOR:
            raise ValueError("Não é possível alterar o coordenador por aqui.")
        if "nome" in dados:
            usuario.nome = dados["nome"]
        if "tipo_perfil" in dados:
            if dados["tipo_perfil"] not in (TipoPerfil.SECRETARIO, TipoPerfil.PADRE):
                raise ValueError("Perfil inválido.")
            usuario.tipo_perfil = dados["tipo_perfil"]
        if "is_active" in dados:
            usuario.is_active = dados["is_active"]
        if dados.get("senha"):
            usuario.set_password(dados["senha"])
            usuario.must_change_password = False
        usuario.save()
        return usuario
