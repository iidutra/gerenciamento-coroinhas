import re

from django.core.management.base import BaseCommand

from apps.scheduling.models import Missa, TipoSlotMissa

PADRAO_DIA13 = re.compile(r"dia\s*13", re.I)


class Command(BaseCommand):
    help = "Corrige tipo_slot das missas do dia 13 cadastradas como Outro."

    def handle(self, *args, **options):
        atualizadas = 0
        for missa in Missa.objects.exclude(tipo_slot=TipoSlotMissa.DIA_13):
            if missa.dia_mes == 13 or PADRAO_DIA13.search(missa.nome or ""):
                missa.tipo_slot = TipoSlotMissa.DIA_13
                if missa.dia_mes is None:
                    missa.dia_mes = 13
                missa.save(update_fields=["tipo_slot", "dia_mes"])
                atualizadas += 1
                self.stdout.write(self.style.SUCCESS(f"Normalizada: {missa.nome} ({missa.horario})"))

        self.stdout.write(self.style.SUCCESS(f"Concluído — {atualizadas} missa(s) normalizada(s)."))
