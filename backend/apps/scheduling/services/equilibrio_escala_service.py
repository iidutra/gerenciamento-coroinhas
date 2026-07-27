"""Controle de equilíbrio semanal e mensal na geração de escalas."""

from collections import defaultdict
from datetime import date, timedelta

from apps.membership.models import Coroinha
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
        self.grupo_fim_semana[sabado] = set(coroinha_ids)

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
        return indisponivel

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
            antigos = self._pool_elegivel(data, exigir_antigo=True)
            novos = self._pool_elegivel(data, exigir_antigo=False)
            selecionados: list[Coroinha] = []
            if antigos:
                selecionados.append(antigos[0])
            if novos:
                novo = novos[0]
                if novo.id not in {c.id for c in selecionados}:
                    selecionados.append(novo)
            if len(selecionados) == 2:
                return selecionados
            pool = self._pool_elegivel(data)
            for c in pool:
                if c.id not in {x.id for x in selecionados}:
                    selecionados.append(c)
                if len(selecionados) >= 2:
                    break
            return selecionados[:2]

        pool = self._pool_elegivel(data)
        return pool[:quantidade]

    def escolher_comunidade(self, data: date, quantidade: int) -> list[Coroinha]:
        pool = self._pool_elegivel(data)
        return pool[:quantidade]
