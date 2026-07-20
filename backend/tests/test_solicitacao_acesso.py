from datetime import date

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.identity.models import TipoPerfil, Usuario
from apps.membership.models import (
    Coroinha,
    Responsavel,
    SolicitacaoAcesso,
    StatusCoroinha,
    StatusSolicitacao,
    Turma,
)

pytestmark = pytest.mark.django_db

# CPF válido de um pai ainda não cadastrado no sistema.
CPF_NOVO_PAI = "39053344705"
SENHA_NOVA = "minhasenha1"


def _verificar(client, nome, data_nascimento):
    return client.post(
        "/api/v1/portal/acesso/verificar",
        {"nome": nome, "data_nascimento": data_nascimento},
        format="json",
    )


def _solicitar(client, coroinha_id, **overrides):
    payload = {
        "coroinha_id": coroinha_id,
        "nome": "João Teste",
        "data_nascimento": "2012-03-15",
        "nome_responsavel": "Novo Pai",
        "cpf": CPF_NOVO_PAI,
        "whatsapp": "69999990000",
        "senha": SENHA_NOVA,
        "confirmar_senha": SENHA_NOVA,
    }
    payload.update(overrides)
    return client.post("/api/v1/portal/acesso/solicitar", payload, format="json")


class TestVerificar:
    def test_encontra_ignorando_acento_e_caixa(self, api_client, coroinha):
        res = _verificar(api_client, "joao   TESTE", "2012-03-15")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data["coroinhas"]) == 1
        assert res.data["coroinhas"][0]["id"] == coroinha.id

    def test_nao_encontra_data_errada(self, api_client, coroinha):
        res = _verificar(api_client, "João Teste", "2011-01-01")
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_nao_encontra_nome_errado(self, api_client, coroinha):
        res = _verificar(api_client, "Outro Nome", "2012-03-15")
        assert res.status_code == status.HTTP_404_NOT_FOUND


class TestSolicitar:
    def test_cria_pedido_pendente_sem_criar_usuario(self, api_client, coroinha):
        res = _solicitar(api_client, coroinha.id)
        assert res.status_code == status.HTTP_201_CREATED
        sol = SolicitacaoAcesso.objects.get()
        assert sol.status == StatusSolicitacao.PENDENTE
        assert sol.cpf == CPF_NOVO_PAI
        # Enquanto não aprovado, nenhuma conta é criada.
        assert not Usuario.objects.filter(cpf=CPF_NOVO_PAI).exists()

    def test_senha_nao_confere(self, api_client, coroinha):
        res = _solicitar(api_client, coroinha.id, confirmar_senha="outra12345")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_cpf_invalido(self, api_client, coroinha):
        res = _solicitar(api_client, coroinha.id, cpf="11111111111")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_bloqueia_pedido_duplicado_pendente(self, api_client, coroinha):
        assert _solicitar(api_client, coroinha.id).status_code == status.HTTP_201_CREATED
        res = _solicitar(api_client, coroinha.id)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "pendente" in res.data["detail"].lower()

    def test_bloqueia_quem_ja_tem_acesso(self, api_client, coroinha, usuario_pai):
        # usuario_pai (CPF_PAI) já é responsável do coroinha da fixture.
        res = _solicitar(api_client, coroinha.id, cpf="11144477735")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "já tem acesso" in res.data["detail"].lower()


class TestAprovacao:
    def test_aprovar_cria_conta_e_permite_login(self, api_client, client_coordenador, coroinha):
        assert _solicitar(api_client, coroinha.id).status_code == status.HTTP_201_CREATED
        sol = SolicitacaoAcesso.objects.get()

        res = client_coordenador.post(f"/api/v1/solicitacoes-acesso/{sol.id}/aprovar/")
        assert res.status_code == status.HTTP_200_OK

        sol.refresh_from_db()
        assert sol.status == StatusSolicitacao.APROVADA

        usuario = Usuario.objects.get(cpf=CPF_NOVO_PAI)
        assert usuario.tipo_perfil == TipoPerfil.PAI
        assert usuario.is_active
        assert usuario.responsavel is not None
        assert usuario.responsavel.coroinhas.filter(id=coroinha.id).exists()

        # Login com CPF + a senha criada no pedido.
        login = api_client.post(
            "/api/v1/auth/login",
            {"identificador": CPF_NOVO_PAI, "senha": SENHA_NOVA},
            format="json",
        )
        assert login.status_code == status.HTTP_200_OK
        assert login.data["usuario"]["tipo_perfil"] == TipoPerfil.PAI

    def test_pai_pode_ter_varios_coroinhas(self, api_client, client_coordenador, coroinha, usuario_pai):
        # Segundo filho do mesmo pai já cadastrado (CPF_PAI / usuario_pai).
        maria = Coroinha.objects.create(
            nome="Maria Teste",
            data_nascimento=date(2014, 5, 10),
            turma=Turma.INICIANTE,
            status=StatusCoroinha.ATIVO,
        )
        res = _solicitar(
            api_client,
            maria.id,
            nome="Maria Teste",
            data_nascimento="2014-05-10",
            cpf="11144477735",
            nome_responsavel="Pai Teste",
        )
        assert res.status_code == status.HTTP_201_CREATED
        sol = SolicitacaoAcesso.objects.get()

        aprovar = client_coordenador.post(f"/api/v1/solicitacoes-acesso/{sol.id}/aprovar/")
        assert aprovar.status_code == status.HTTP_200_OK

        # Não cria conta duplicada: continua o mesmo usuario_pai.
        assert Usuario.objects.filter(cpf="11144477735").count() == 1
        usuario_pai.refresh_from_db()
        assert usuario_pai.responsavel.coroinhas.count() == 2

        # Portal lista os dois filhos.
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(usuario_pai)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        filhos = api_client.get("/api/v1/portal/filhos")
        assert filhos.status_code == status.HTTP_200_OK
        assert len(filhos.data) == 2

    def test_rejeitar_nao_cria_conta(self, api_client, client_coordenador, coroinha):
        _solicitar(api_client, coroinha.id)
        sol = SolicitacaoAcesso.objects.get()
        res = client_coordenador.post(f"/api/v1/solicitacoes-acesso/{sol.id}/rejeitar/")
        assert res.status_code == status.HTTP_200_OK
        sol.refresh_from_db()
        assert sol.status == StatusSolicitacao.REJEITADA
        assert not Usuario.objects.filter(cpf=CPF_NOVO_PAI).exists()

    def test_nao_reprocessa(self, api_client, client_coordenador, coroinha):
        _solicitar(api_client, coroinha.id)
        sol = SolicitacaoAcesso.objects.get()
        client_coordenador.post(f"/api/v1/solicitacoes-acesso/{sol.id}/aprovar/")
        res = client_coordenador.post(f"/api/v1/solicitacoes-acesso/{sol.id}/aprovar/")
        assert res.status_code == status.HTTP_400_BAD_REQUEST


class TestContagemPendentes:
    def test_conta_apenas_pendentes(self, api_client, client_coordenador, coroinha):
        # Zero no início.
        res = client_coordenador.get("/api/v1/solicitacoes-acesso/pendentes-count/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["pendentes"] == 0

        _solicitar(api_client, coroinha.id)
        res = client_coordenador.get("/api/v1/solicitacoes-acesso/pendentes-count/")
        assert res.data["pendentes"] == 1

        # Após aprovar, volta a zero.
        sol = SolicitacaoAcesso.objects.get()
        client_coordenador.post(f"/api/v1/solicitacoes-acesso/{sol.id}/aprovar/")
        res = client_coordenador.get("/api/v1/solicitacoes-acesso/pendentes-count/")
        assert res.data["pendentes"] == 0

    def test_contagem_exige_autenticacao(self, api_client):
        res = api_client.get("/api/v1/solicitacoes-acesso/pendentes-count/")
        assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class TestPermissoes:
    def test_publico_pode_verificar_e_solicitar(self, api_client, coroinha):
        assert _verificar(api_client, "João Teste", "2012-03-15").status_code == status.HTTP_200_OK
        assert _solicitar(api_client, coroinha.id).status_code == status.HTTP_201_CREATED

    def test_lista_exige_staff(self, api_client):
        res = api_client.get("/api/v1/solicitacoes-acesso/")
        assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_padre_lista_mas_nao_aprova(self, api_client, client_padre, coroinha):
        _solicitar(api_client, coroinha.id)
        sol = SolicitacaoAcesso.objects.get()
        assert client_padre.get("/api/v1/solicitacoes-acesso/").status_code == status.HTTP_200_OK
        res = client_padre.post(f"/api/v1/solicitacoes-acesso/{sol.id}/aprovar/")
        assert res.status_code == status.HTTP_403_FORBIDDEN
