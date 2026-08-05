from datetime import date
from unittest.mock import patch

import pytest

from apps.communication.services.aniversario_service import AniversarioService
from apps.membership.models import Coroinha, StatusCoroinha, Turma

HOJE = date(2026, 8, 5)


@pytest.fixture
def aniversariante_hoje(db):
    return Coroinha.objects.create(
        nome="Maria Aniversário",
        data_nascimento=date(2014, 8, 5),  # faz 12 em 05/08/2026
        telefone="(69) 99999-1111",
        turma=Turma.INICIANTE,
        status=StatusCoroinha.ATIVO,
    )


@pytest.fixture
def outro_dia(db):
    return Coroinha.objects.create(
        nome="Pedro Outro",
        data_nascimento=date(2013, 8, 6),
        turma=Turma.INICIANTE,
        status=StatusCoroinha.ATIVO,
    )


@pytest.mark.django_db
class TestAniversarioService:
    def test_encontra_apenas_do_dia(self, aniversariante_hoje, outro_dia):
        nomes = [c.nome for c in AniversarioService.aniversariantes(HOJE)]
        assert nomes == ["Maria Aniversário"]

    def test_ignora_inativo(self, aniversariante_hoje):
        aniversariante_hoje.status = StatusCoroinha.INATIVO
        aniversariante_hoje.save()
        assert AniversarioService.aniversariantes(HOJE) == []

    def test_mensagem_tem_nome_idade_e_telefone(self, aniversariante_hoje):
        corpo = AniversarioService.montar_mensagem(
            AniversarioService.aniversariantes(HOJE), HOJE
        )
        assert "05/08" in corpo
        assert "Maria Aniversário — 12 anos" in corpo
        assert "(69) 99999-1111" in corpo

    def test_usa_telefone_da_mae_quando_sem_telefone_proprio(self, db):
        c = Coroinha.objects.create(
            nome="Sem Telefone",
            data_nascimento=date(2015, 8, 5),
            telefone_mae="(69) 98888-2222",
            status=StatusCoroinha.ATIVO,
        )
        corpo = AniversarioService.montar_mensagem([c], HOJE)
        assert "(69) 98888-2222" in corpo

    def test_notificar_envia_para_destino(self, settings, aniversariante_hoje):
        settings.NOTIFICACAO_ANIVERSARIO_DESTINO = "69992690072"
        with patch(
            "apps.communication.services.aniversario_service.WhatsAppService.enviar",
            return_value=True,
        ) as mock_enviar:
            resultado = AniversarioService.notificar(HOJE)
        assert resultado["enviado"] is True
        assert resultado["aniversariantes"] == 1
        numero, corpo = mock_enviar.call_args[0]
        assert numero == "69992690072"
        assert "Maria Aniversário" in corpo

    def test_notificar_sem_destino(self, settings, aniversariante_hoje):
        settings.NOTIFICACAO_ANIVERSARIO_DESTINO = ""
        resultado = AniversarioService.notificar(HOJE)
        assert resultado == {"enviado": False, "motivo": "sem_destino", "aniversariantes": 0}

    def test_notificar_sem_aniversariante(self, settings, outro_dia):
        settings.NOTIFICACAO_ANIVERSARIO_DESTINO = "69992690072"
        with patch(
            "apps.communication.services.aniversario_service.WhatsAppService.enviar"
        ) as mock_enviar:
            resultado = AniversarioService.notificar(HOJE)
        assert resultado["motivo"] == "nenhum_aniversariante"
        mock_enviar.assert_not_called()
