from datetime import time

from django.core.management.base import BaseCommand

from apps.scheduling.models import (
    DiaSemana,
    LocalCelebracao,
    Missa,
    TipoSlotMissa,
)

MISSAS_PADRAO = [
    # Fim de semana — Santuário (grupos rotativos)
    ("Sábado 18h30", DiaSemana.SABADO, None, time(18, 30), TipoSlotMissa.SABADO_NOITE, LocalCelebracao.SANTUARIO),
    ("Domingo 08h", DiaSemana.DOMINGO, None, time(8, 0), TipoSlotMissa.DOMINGO_MANHA, LocalCelebracao.SANTUARIO),
    ("Domingo 18h30", DiaSemana.DOMINGO, None, time(18, 30), TipoSlotMissa.DOMINGO_NOITE, LocalCelebracao.SANTUARIO),
    # Sexta — Adoração + Missa
    ("Sexta 18h", DiaSemana.SEXTA, None, time(18, 0), TipoSlotMissa.SEXTA_ADORACAO, LocalCelebracao.SANTUARIO),
    # Quarta — Voluntários (sem escala automática)
    ("Quarta 19h", DiaSemana.QUARTA, None, time(19, 0), TipoSlotMissa.QUARTA_VOLUNTARIOS, LocalCelebracao.SANTUARIO),
    # Comunidade Santo Antônio
    (
        "Comunidade — Domingo 10h30",
        DiaSemana.DOMINGO,
        None,
        time(10, 30),
        TipoSlotMissa.COMUNIDADE_DOMINGO,
        LocalCelebracao.COMUNIDADE,
    ),
    # Dia 13 — cadastro manual (não entra na geração automática)
    ("Dia 13 — 06h", None, 13, time(6, 0), TipoSlotMissa.DIA_13, LocalCelebracao.SANTUARIO),
    ("Dia 13 — 09h", None, 13, time(9, 0), TipoSlotMissa.DIA_13, LocalCelebracao.SANTUARIO),
    ("Dia 13 — 12h", None, 13, time(12, 0), TipoSlotMissa.DIA_13, LocalCelebracao.SANTUARIO),
    ("Dia 13 — 18h", None, 13, time(18, 0), TipoSlotMissa.DIA_13, LocalCelebracao.SANTUARIO),
]


class Command(BaseCommand):
    help = "Cria ou atualiza missas padrão da paróquia."

    def handle(self, *args, **options):
        for nome, dia_semana, dia_mes, horario, tipo_slot, local in MISSAS_PADRAO:
            _, created = Missa.objects.update_or_create(
                nome=nome,
                defaults={
                    "dia_semana": dia_semana,
                    "dia_mes": dia_mes,
                    "horario": horario,
                    "ativa": True,
                    "tipo_slot": tipo_slot,
                    "local": local,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Missa criada: {nome}"))
            else:
                self.stdout.write(f"Missa atualizada: {nome}")
