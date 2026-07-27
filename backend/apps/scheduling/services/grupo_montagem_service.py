"""Monta grupos mensais mesclando idade, antigos/novos e bairro."""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.membership.models import Coroinha, StatusCoroinha
from apps.scheduling.models import EscalaItem

BAIRROS_PV = (
    "areal",
    "cohab",
    "floresta",
    "cuniã",
    "cunia",
    "embraer",
    "olímpico",
    "olimpico",
    "triângulo",
    "triangulo",
    "são cristóvão",
    "sao cristovao",
    "mocambo",
    "caladinho",
    "nova porto velho",
    "centro",
    "industrial",
    "tancredo neves",
    "lagoinha",
    "cidade do lobo",
    "eletronorte",
    "rodovelho",
    "lagoa",
    "cascalheira",
)

ROTACAO_FIM_DE_SEMANA = [
    {"sabado": 2, "dom_manha": 3, "dom_noite": 4},
    {"sabado": 1, "dom_manha": 2, "dom_noite": 3},
    {"sabado": 4, "dom_manha": 1, "dom_noite": 2},
    {"sabado": 3, "dom_manha": 4, "dom_noite": 1},
]


def extrair_bairro(endereco: str) -> str:
    texto = (endereco or "").lower()
    for bairro in BAIRROS_PV:
        if bairro in texto:
            return bairro.replace("ã", "a").replace("ó", "o").replace("ç", "c")
    return "outros"


def faixa_etaria(idade: int) -> str:
    if idade <= 11:
        return "8-11"
    if idade <= 14:
        return "12-14"
    return "15-18"


class GrupoMontagemService:
    NUM_GRUPOS = 4

    @classmethod
    def candidatos(cls) -> list[Coroinha]:
        return list(
            Coroinha.objects.filter(status__in=[StatusCoroinha.ATIVO, StatusCoroinha.EM_FORMACAO]).order_by(
                "nome"
            )
        )

    @classmethod
    def _contagem_servicos(cls, coroinha_ids: list[int]) -> dict[int, int]:
        desde = timezone.now().date() - timedelta(days=120)
        rows = (
            EscalaItem.objects.filter(
                coroinha_id__in=coroinha_ids,
                escala__data__gte=desde,
            )
            .values("coroinha_id")
            .annotate(total=Count("id"))
        )
        return {r["coroinha_id"]: r["total"] for r in rows}

    @classmethod
    def montar_grupos(cls, tamanho_grupo: int) -> dict[int, list[Coroinha]]:
        """Retorna {1: [coroinhas...], 2: [...], ...} com até 4 grupos."""
        candidatos = cls.candidatos()
        if not candidatos:
            return {}

        necessarios = tamanho_grupo * cls.NUM_GRUPOS
        if len(candidatos) < necessarios:
            raise ValueError(
                f"São necessários pelo menos {necessarios} coroinhas ativos "
                f"({cls.NUM_GRUPOS} grupos × {tamanho_grupo}). Há {len(candidatos)}."
            )

        scores = cls._contagem_servicos([c.id for c in candidatos])
        ordenados = sorted(candidatos, key=lambda c: (scores.get(c.id, 0), c.nome))

        grupos: dict[int, list[Coroinha]] = {i: [] for i in range(1, cls.NUM_GRUPOS + 1)}
        bairros_por_grupo: dict[int, set[str]] = {i: set() for i in range(1, cls.NUM_GRUPOS + 1)}
        faixas_por_grupo: dict[int, set[str]] = {i: set() for i in range(1, cls.NUM_GRUPOS + 1)}
        antigos_por_grupo: dict[int, int] = defaultdict(int)

        pool = list(ordenados[:necessarios])

        for coroinha in pool:
            bairro = extrair_bairro(coroinha.endereco)
            faixa = faixa_etaria(coroinha.idade)

            def pontuacao_grupo(g: int) -> tuple:
                membros = len(grupos[g])
                if membros >= tamanho_grupo:
                    return (999, 0, 0, 0)
                bairro_bonus = 0 if bairro in bairros_por_grupo[g] or bairro == "outros" else 1
                faixa_bonus = 0 if faixa in faixas_por_grupo[g] else 1
                antigo_bonus = 0 if coroinha.antigo and antigos_por_grupo[g] == 0 else 1
                if not coroinha.antigo and antigos_por_grupo[g] >= max(1, membros // 2):
                    antigo_bonus = -1
                return (membros, bairro_bonus, faixa_bonus, antigo_bonus)

            escolhido = min(range(1, cls.NUM_GRUPOS + 1), key=pontuacao_grupo)
            grupos[escolhido].append(coroinha)
            bairros_por_grupo[escolhido].add(bairro)
            faixas_por_grupo[escolhido].add(faixa)
            if coroinha.antigo:
                antigos_por_grupo[escolhido] += 1

        return grupos
