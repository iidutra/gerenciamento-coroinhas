from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Prepara armazenamento de mídia (diretório local ou bucket S3/R2)."

    def handle(self, *args, **options):
        if getattr(settings, "USE_S3", False):
            call_command("setup_minio")
            self.stdout.write(self.style.SUCCESS("Storage S3/R2 verificado."))
            return

        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        self.stdout.write(self.style.SUCCESS(f"Diretório de mídia pronto: {media_root}"))
