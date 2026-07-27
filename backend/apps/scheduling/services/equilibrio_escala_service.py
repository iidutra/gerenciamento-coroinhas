"""Controle de equilíbrio semanal e mensal na geração de escalas."""

from collections import defaultdict
from datetime import date, timedelta

from apps.membership.models import Coroinha
from apps.membership.services.gemeos_service import GemeosService
from apps.scheduling.services.grupo_montagem_service import GrupoMontagemService


class ControleEquilibrioMensal:
    """Evita sobrecarga na mesma semana e prioriza quem serviu menos."""

    def __init__(self, candidatos: list[Coroinha]):
        self.candidatos = candidatos
        self.historico = GrupoMontagemService._contagem_servicos([c.id for c in candidatos])
        self.mes: dict[int, int] = defaultdict(int)
        self.semana: dict[tuple[int, int], set[int]] = defaultdict(set)
        self.grupo_fim_semana: dict[date, set[int]] = {}

    @staticmethod
    def chave_semana(data: date) -> tuple[int, int]:
        iso = data.isocalendar()
        return (iso[0], iso[1])

    def registrar_grupo_fim_semana(self, sabado: date, coroinha_ids: list[int]) -> None:
        self.grupo_fim_semana[sabado] = GemeosService.expandir_ids(set(coroinha_ids))

    def registrar_servicos(self, data: date, coroinha_ids: list[int]) -> None:
        key = self.chave_semana(data)
        for cid in coroinha_ids:
            self.mes[cid] += 1
            self.semana[key].add(cid)

    def ids_indisponiveis(self, data: date, *, incluir_grupo_fim_semana: bool = True) -> set[int]:
        """Coroinhas que já serviram na semana ou no fim de semana seguinte (grupo)."""
        indisponivel = set(self.semana.get(self.chave_semana(data), set()))
        if incluir_grupo_fim_semana and data.weekday() == 4:
            sabado = data + timedelta(days=1)
            indisponivel |= self.grupo_fim_semana.get(sabado, set())
        if incluir_grupo_fim_semana and data.weekday() == 6:
            sabado = data - timedelta(days=1)
            indisponivel |= self.grupo_fim_semana.get(sabado, set())
        return GemeosService.expandir_ids(indisponivel)

    def _tentar_unidade_familiar(self, pool: list[Coroinha], quantidade: int) -> list[Coroinha] | None:
        return GemeosService.selecionar_da_familia(
            pool,
            quantidade,
            candidatos=self.candidatos,
        )

    def _pontuacao(self, coroinha: Coroinha) -> tuple:
        return (self.mes.get(coroinha.id, 0), self.historico.get(coroinha.id, 0), coroinha.nome)

    def _pool_elegivel(
        self,
        data: date,
        *,
        incluir_grupo_fim_semana: bool = True,
        exigir_antigo: bool | None = None,
    ) -> list[Coroinha]:
        indisponivel = self.ids_indisponiveis(data, incluir_grupo_fim_semana=incluir_grupo_fim_semana)
        pool = [c for c in self.candidatos if c.id not in indisponivel]
        if exigir_antigo is True:
            pool = [c for c in pool if c.antigo]
        elif exigir_antigo is False:
            pool = [c for c in pool if not c.antigo]
        return sorted(pool, key=self._pontuacao)

    def escolher_sexta(self, data: date, quantidade: int = 2) -> list[Coroinha]:
        """Sexta: rotativo com 1 antigo + 1 novo (quando quantidade=2)."""
        if quantidade == 2:
            pool_completo = self._pool_elegivel(data)
            par_gemeos = self._tentar_unidade_familiar(pool_completo, quantidade)
            if par_gemeos:
                return par_gemeos

            antigos = self._pool_elegivel(data, exigir_antigo=True)
            novos = self._pool_elegivel(data, exigir_antigo=False)
            selecionados: list[Coroinha] = []
            if antigos:
                selecionados.append(antigos[0])
            if novos:
                novo = novos[0]
                if novo.id not in {c.id for c in selecionados}:
                    selecionados.append(novo)
            selecionados = GemeosService.completar_selecao(selecionados, pool_completo)
            if len(selecionados) == 2:
                return selecionados[:2]
            pool = pool_completo
            for c in pool:
                if c.id not in {x.id for x in selecionados}:
                    selecionados.append(c)
                if len(selecionados) >= 2:
                    break
            return selecionados[:2]

        pool = self._pool_elegivel(data)
        selecionados = pool[:quantidade]
        return GemeosService.completar_selecao(selecionados, pool)

    def escolher_comunidade(self, data: date, quantidade: int) -> list[Coroinha]:
        pool = self._pool_elegivel(data)
        if quantidade >= 2:
            par_gemeos = self._tentar_unidade_familiar(pool, min(2, quantidade))
            if par_gemeos and quantidade == 2:
                return par_gemeos
        selecionados = pool[:quantidade]
        return GemeosService.completar_selecao(selecionados, pool)
