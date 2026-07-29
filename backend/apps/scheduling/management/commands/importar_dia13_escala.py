import unicodedata
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.identity.models import Usuario
from apps.membership.models import Coroinha, StatusCoroinha
from apps.scheduling.models import Escala, Missa, ModoEscala, TipoSlotMissa
from apps.scheduling.services.escala_service import EscalaService

# Escala manual do dia 13/08/2026 — nomes parciais; "?" = vaga em aberto
ESCALA_DIA13_AGOSTO_2026: dict[int, list[str]] = {
    6: [
        "Luís victor",
        "Daiana",
        "Maria Julia",
        "Davi Lucca",
        "Anna Clara Barbosa",
        "Isabel Dionísio",
    ],
    9: [
        "Vitor Calixto",
        "Carlos Henrique",
    ],
    12: [
        "Franciele",
        "Maria Luiza",
        "Juliana Oliveira",
    ],
    18: [
        "Anna Clara Barbosa",
        "Fabrine",
        "Ana Cecília",
        "Lohana Beatriz",
        "Esther Damazio",
        "Valentina Damázio",
    ],
}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower().strip()


def buscar_coroinha(nome_busca: str, coroinhas: list[Coroinha]) -> Coroinha | None:
    if not nome_busca or nome_busca.strip() in ("?", "—", "-"):
        return None

    alvo = normalizar(nome_busca)
    tokens = [t for t in alvo.split() if len(t) > 1]

    for coroinha in coroinhas:
        if normalizar(coroinha.nome) == alvo:
            return coroinha

    parciais = [
        c
        for c in coroinhas
        if alvo in normalizar(c.nome) or normalizar(c.nome).startswith(alvo)
    ]
    if len(parciais) == 1:
        return parciais[0]

    if tokens:
        candidatos = [
            c for c in coroinhas if all(token in normalizar(c.nome) for token in tokens)
        ]
        if len(candidatos) == 1:
            return candidatos[0]

    return None


class Command(BaseCommand):
    help = "Importa escala manual do dia 13 (Solenidade) para um mês."

    def add_arguments(self, parser):
        parser.add_argument("ano", type=int)
        parser.add_argument("mes", type=int)
        parser.add_argument(
            "--substituir",
            action="store_true",
            help="Remove escalas existentes do dia 13 antes de importar.",
        )
        parser.add_argument(
            "--preset",
            default="agosto-2026",
            choices=["agosto-2026"],
            help="Lista pré-definida de nomes.",
        )

    def handle(self, *args, **options):
        ano = options["ano"]
        mes = options["mes"]
        dia = date(ano, mes, 13)

        usuario = Usuario.objects.filter(is_active=True).order_by("id").first()
        if not usuario:
            raise CommandError("Nenhum usuário ativo encontrado para registrar a escala.")

        if options["preset"] != "agosto-2026" or (ano, mes) != (2026, 8):
            raise CommandError("Preset disponível apenas para agosto/2026.")

        coroinhas = list(
            Coroinha.objects.filter(status__in=[StatusCoroinha.ATIVO, StatusCoroinha.EM_FORMACAO])
        )
        if not coroinhas:
            raise CommandError("Nenhum coroinha cadastrado.")

        missas_dia13 = {
            m.horario.hour: m
            for m in Missa.objects.filter(tipo_slot=TipoSlotMissa.DIA_13, dia_mes=13)
        }
        for hora in (6, 9, 12, 18):
            if hora not in missas_dia13:
                raise CommandError(
                    f"Missa do dia 13 às {hora}h não encontrada. Execute: python manage.py setup_missas"
                )

        if options["substituir"]:
            removidas = Escala.objects.filter(
                data=dia,
                missa__tipo_slot=TipoSlotMissa.DIA_13,
            ).count()
            Escala.objects.filter(data=dia, missa__tipo_slot=TipoSlotMissa.DIA_13).delete()
            self.stdout.write(f"Removidas {removidas} escala(s) do dia 13.")

        criadas = 0
        for hora, nomes in ESCALA_DIA13_AGOSTO_2026.items():
            missa = missas_dia13[hora]
            if Escala.objects.filter(data=dia, missa=missa).exists():
                self.stdout.write(f"Pulando {missa.nome} — já existe escala.")
                continue

            ids: list[int] = []
            nao_encontrados: list[str] = []
            for nome in nomes:
                coroinha = buscar_coroinha(nome, coroinhas)
                if coroinha:
                    ids.append(coroinha.id)
                else:
                    nao_encontrados.append(nome)

            if not ids:
                self.stdout.write(self.style.WARNING(f"{missa.nome}: nenhum coroinha encontrado."))
                continue

            EscalaService.montar(
                data=dia,
                missa_id=missa.id,
                modo=ModoEscala.SELECAO_MANUAL,
                quantidade=len(ids),
                usuario=usuario,
                coroinha_ids=ids,
            )
            criadas += 1
            self.stdout.write(self.style.SUCCESS(f"{missa.nome}: {len(ids)} coroinha(s)"))
            for nome in nao_encontrados:
                self.stdout.write(self.style.WARNING(f"  Não encontrado: {nome}"))

        self.stdout.write(self.style.SUCCESS(f"Importação concluída — {criadas} missa(s) do dia 13."))
