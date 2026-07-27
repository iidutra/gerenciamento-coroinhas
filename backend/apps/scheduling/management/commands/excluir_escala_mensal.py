from django.core.management.base import BaseCommand

from apps.scheduling.models import EscalaMensal


class Command(BaseCommand):
    help = "Exclui escala mensal por ano/mês."

    def add_arguments(self, parser):
        parser.add_argument("ano", type=int)
        parser.add_argument("mes", type=int)

    def handle(self, *args, **options):
        em = EscalaMensal.objects.filter(ano=options["ano"], mes=options["mes"]).first()
        if not em:
            self.stdout.write("Escala mensal não encontrada.")
            return
        total = em.escalas.count()
        em.escalas.all().delete()
        em.delete()
        self.stdout.write(self.style.SUCCESS(f"Excluída escala {options['mes']:02d}/{options['ano']} ({total} celebrações)."))
