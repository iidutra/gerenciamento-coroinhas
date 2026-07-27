"""Testes do controle de equilíbrio de escalas."""

from datetime import date

import pytest

from apps.membership.models import Coroinha, StatusCoroinha, Turma
from apps.scheduling.services.equilibrio_escala_service import ControleEquilibrioMensal

pytestmark = pytest.mark.django_db


@pytest.fixture
def pool(db):
    lista = []
    for i in range(10):
        lista.append(
            Coroinha.objects.create(
                nome=f"C {i + 1}",
                data_nascimento=date(2012, 1, 1),
                status=StatusCoroinha.ATIVO,
                antigo=(i < 4),
            )
        )
    return lista


class TestControleEquilibrio:
    def test_sexta_escolhe_antigo_e_novo(self, pool):
        controle = ControleEquilibrioMensal(pool)
        sexta = date(2026, 7, 3)
        par = controle.escolher_sexta(sexta, quantidade=2)
        assert len(par) == 2
        assert par[0].antigo != par[1].antigo

    def test_exclui_grupo_fim_de_semana(self, pool):
        controle = ControleEquilibrioMensal(pool)
        sabado = date(2026, 7, 4)
        controle.registrar_grupo_fim_semana(sabado, [pool[0].id, pool[1].id])
        sexta = date(2026, 7, 3)
        par = controle.escolher_sexta(sexta, quantidade=2)
        ids = {c.id for c in par}
        assert pool[0].id not in ids
        assert pool[1].id not in ids

    def test_prioriza_quem_serviu_menos(self, pool):
        controle = ControleEquilibrioMensal(pool)
        controle.registrar_servicos(date(2026, 7, 1), [pool[2].id, pool[3].id])
        sexta = date(2026, 7, 10)
        par = controle.escolher_sexta(sexta, quantidade=2)
        ids = {c.id for c in par}
        assert pool[2].id not in ids or pool[3].id not in ids
