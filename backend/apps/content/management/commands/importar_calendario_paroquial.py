from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.content.services.calendario_import_service import (
    DEFAULT_ARQUIVO,
    CalendarioImportService,
)
from apps.identity.models import TipoPerfil, Usuario


class Command(BaseCommand):
    help = (
        "Importa eventos do calendário paroquial (coroinhas) para notícias e formações. "
        "Dados extraídos do PDF PEPS - Calendário Paroquial na raiz do projeto."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--arquivo",
            type=str,
            default=str(DEFAULT_ARQUIVO),
            help="Caminho do JSON com eventos (padrão: apps/content/data/calendario_paroquial_2026_coroinhas.json)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a importação sem gravar no banco",
        )
        parser.add_argument(
            "--sem-missas",
            action="store_true",
            help="Não executa setup_missas (missas recorrentes do dia 13)",
        )

    def handle(self, *args, **options):
        arquivo = Path(options["arquivo"])
        if not arquivo.is_file():
            self.stderr.write(self.style.ERROR(f"Arquivo não encontrado: {arquivo}"))
            return

        if not options["sem_missas"] and not options["dry_run"]:
            self.stdout.write("Garantindo missas recorrentes (dia 13 e domingos)...")
            call_command("setup_missas")

        autor = Usuario.objects.filter(tipo_perfil=TipoPerfil.COORDENADOR, is_active=True).first()

        payload = CalendarioImportService.carregar_arquivo(arquivo)
        self.stdout.write(f"Fonte: {payload.get('fonte', arquivo.name)}")
        self.stdout.write(f"Eventos no arquivo: {len(payload.get('eventos', []))}")

        stats = CalendarioImportService.importar(
            caminho=arquivo,
            autor=autor,
            dry_run=options["dry_run"],
        )

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run — nenhum dado gravado."))

        self.stdout.write(
            self.style.SUCCESS(
                "Importação concluída: "
                f"{stats['noticias_criadas']} notícias novas, "
                f"{stats['noticias_atualizadas']} notícias atualizadas, "
                f"{stats['formacoes_criadas']} formações novas, "
                f"{stats['formacoes_atualizadas']} formações atualizadas."
                + (
                    f" ({stats['noticias_legadas_removidas']} notícias legadas removidas.)"
                    if stats.get("noticias_legadas_removidas")
                    else ""
                )
            )
        )
