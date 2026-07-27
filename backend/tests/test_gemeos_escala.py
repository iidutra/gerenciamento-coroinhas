"""Testes de gêmeos na escala."""

from datetime import date, time

import pytest

from apps.membership.models import Coroinha, StatusCoroinha, Turma
from apps.membership.services.gemeos_service import GemeosService, extrair_sobrenome
from apps.scheduling.models import DiaSemana, Escala, Missa, ModoEscala
from apps.scheduling.services.equilibrio_escala_service import ControleEquilibrioMensal
from apps.scheduling.services.escala_service import EscalaService
from apps.scheduling.services.grupo_montagem_service import GrupoMontagemService

pytestmark = pytest.mark.django_db


@pytest.fixture
def gemeos(db):
    a = Coroinha.objects.create(
        nome="Gêmeo A",
        data_nascimento=date(2012, 3, 10),
        nome_mae="Maria Silva",
        status=StatusCoroinha.ATIVO,
        antigo=True,
        endereco="Centro",
    )
    b = Coroinha.objects.create(
        nome="Gêmeo B",
        data_nascimento=date(2012, 3, 10),
        nome_mae="Maria Silva",
        gemeo_de=a,
        status=StatusCoroinha.ATIVO,
        antigo=False,
        endereco="Centro",
    )
    return a, b


@pytest.fixture
def coroinhas_com_gemeos(db, gemeos):
    lista = list(gemeos)
    for i in range(34):
        lista.append(
            Coroinha.objects.create(
                nome=f"Outro {i + 1:02d}",
                data_nascimento=date(2010 + (i % 8), 1, 15),
                turma=Turma.INTERMEDIARIO,
                status=StatusCoroinha.ATIVO,
                antigo=(i % 3 == 0),
                endereco="Centro" if i % 2 == 0 else "Cohab",
            )
        )
    return lista


class TestGemeosService:
    def test_par_gemeo_bidirecional(self, gemeos):
        a, b = gemeos
        assert GemeosService.par_gemeo(a).id == b.id
        assert GemeosService.par_gemeo(b).id == a.id

    def test_unidades_agrupa_par(self, gemeos, coroinhas_com_gemeos):
        unidades = GemeosService.unidades(coroinhas_com_gemeos)
        par = next(u for u in unidades if len(u) == 2)
        ids = {c.id for c in par}
        assert ids == {gemeos[0].id, gemeos[1].id}

    def test_validar_conjunto_rejeita_split(self, gemeos):
        a, _ = gemeos
        with pytest.raises(ValueError, match="Gêmeos e irmãos"):
            GemeosService.validar_conjunto([a.id])

    def test_validar_conjunto_aceita_par(self, gemeos):
        a, b = gemeos
        GemeosService.validar_conjunto([a.id, b.id])


class TestGrupoMontagemGemeos:
    def test_gemeos_no_mesmo_grupo(self, coroinhas_com_gemeos, gemeos):
        grupos = GrupoMontagemService.montar_grupos(tamanho_grupo=9)
        a, b = gemeos
        grupo_a = next(n for n, membros in grupos.items() if any(c.id == a.id for c in membros))
        grupo_b = next(n for n, membros in grupos.items() if any(c.id == b.id for c in membros))
        assert grupo_a == grupo_b


class TestEquilibrioGemeos:
    def test_sexta_prefere_par_gemeos(self, gemeos):
        a, b = gemeos
        pool = [a, b] + [
            Coroinha.objects.create(
                nome=f"Extra {i}",
                data_nascimento=date(2011, 1, 1),
                status=StatusCoroinha.ATIVO,
                antigo=(i == 0),
            )
            for i in range(8)
        ]
        controle = ControleEquilibrioMensal(pool)
        sexta = date(2026, 8, 7)
        par = controle.escolher_sexta(sexta, quantidade=2)
        ids = {c.id for c in par}
        assert a.id in ids and b.id in ids

    def test_indisponivel_inclui_gemeo(self, gemeos):
        a, b = gemeos
        pool = list(gemeos) + [
            Coroinha.objects.create(
                nome=f"C {i}",
                data_nascimento=date(2011, 1, 1),
                status=StatusCoroinha.ATIVO,
            )
            for i in range(8)
        ]
        controle = ControleEquilibrioMensal(pool)
        sabado = date(2026, 8, 8)
        controle.registrar_grupo_fim_semana(sabado, [a.id])
        sexta = date(2026, 8, 7)
        indisponivel = controle.ids_indisponiveis(sexta)
        assert a.id in indisponivel
        assert b.id in indisponivel


class TestDefinirMembrosGemeos:
    def test_rejeita_gemeo_sem_par(self, gemeos):
        a, _ = gemeos
        missa = Missa.objects.create(
            nome="Teste",
            dia_semana=DiaSemana.DOMINGO,
            horario=time(8, 0),
            ativa=True,
        )
        escala = Escala.objects.create(
            data=date(2026, 8, 10),
            missa=missa,
            modo=ModoEscala.SELECAO_MANUAL,
        )
        with pytest.raises(ValueError, match="Gêmeos e irmãos"):
            EscalaService.definir_membros(escala, [a.id])


class TestIrmaosService:
    def test_extrair_sobrenome_nomes_reais(self):
        assert extrair_sobrenome("Valentina Damazio Moterle") == "damazio moterle"
        assert extrair_sobrenome("Esther Damazio Moterle") == "damazio moterle"
        assert extrair_sobrenome("Carlos Henrique Siqueira de Carlos") == "siqueira de carlos"
        assert extrair_sobrenome("Maria Luíza Siqueira de Carlos") == "siqueira de carlos"

    @pytest.fixture
    def irmaos(self, db):
        a = Coroinha.objects.create(
            nome="Pedro Silva Santos",
            data_nascimento=date(2012, 1, 10),
            status=StatusCoroinha.ATIVO,
        )
        b = Coroinha.objects.create(
            nome="Ana Silva Santos",
            data_nascimento=date(2014, 6, 20),
            status=StatusCoroinha.ATIVO,
        )
        c = Coroinha.objects.create(
            nome="Lucas Silva Santos",
            data_nascimento=date(2016, 3, 5),
            status=StatusCoroinha.ATIVO,
        )
        return a, b, c

    def test_detecta_irmaos_por_sobrenome(self, irmaos):
        a, b, c = irmaos
        familia = GemeosService.familia_ids(a.id, list(irmaos))
        assert familia == {a.id, b.id, c.id}

    def test_moterle_e_siqueira_de_carlos(self, db):
        valentina = Coroinha.objects.create(
            nome="Valentina Damazio Moterle",
            data_nascimento=date(2012, 5, 1),
            status=StatusCoroinha.ATIVO,
        )
        esther = Coroinha.objects.create(
            nome="Esther Damazio Moterle",
            data_nascimento=date(2012, 5, 1),
            status=StatusCoroinha.ATIVO,
        )
        carlos = Coroinha.objects.create(
            nome="Carlos Henrique Siqueira de Carlos",
            data_nascimento=date(2011, 3, 1),
            status=StatusCoroinha.ATIVO,
        )
        maria = Coroinha.objects.create(
            nome="Maria Luíza Siqueira de Carlos",
            data_nascimento=date(2013, 8, 1),
            status=StatusCoroinha.ATIVO,
        )
        assert GemeosService.familia_ids(valentina.id, [valentina, esther, carlos, maria]) == {
            valentina.id,
            esther.id,
        }
        assert GemeosService.familia_ids(carlos.id, [valentina, esther, carlos, maria]) == {
            carlos.id,
            maria.id,
        }

    def test_nao_agrupa_sobrenome_diferente(self, db):
        a = Coroinha.objects.create(
            nome="Pedro Silva Santos",
            data_nascimento=date(2012, 1, 10),
            status=StatusCoroinha.ATIVO,
        )
        b = Coroinha.objects.create(
            nome="Ana Oliveira Santos",
            data_nascimento=date(2014, 6, 20),
            status=StatusCoroinha.ATIVO,
        )
        familia = GemeosService.familia_ids(a.id, [a, b])
        assert familia == {a.id}

    def test_unidades_agrupa_tres_irmaos(self, irmaos):
        unidades = GemeosService.unidades(list(irmaos))
        assert len(unidades) == 1
        assert len(unidades[0]) == 3
