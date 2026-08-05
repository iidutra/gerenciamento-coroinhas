from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.communication.services.aniversario_service import AniversarioService


class Command(BaseCommand):
    help = "Envia ao coordenador (WhatsApp) os coroinhas aniversariantes de hoje."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data",
            help="Data de referência no formato AAAA-MM-DD (padrão: hoje).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas mostra a mensagem, sem enviar.",
        )

    def handle(self, *args, **options):
        if options.get("data"):
            try:
                ref = date.fromisoformat(options["data"])
            except ValueError as exc:
                raise CommandError(f"Data inválida: {options['data']}") from exc
        else:
            ref = date.today()

        coroinhas = AniversarioService.aniversariantes(ref)
        if not coroinhas:
            self.stdout.write(f"Nenhum aniversariante em {ref.strftime('%d/%m')}.")
            return

        self.stdout.write(AniversarioService.montar_mensagem(coroinhas, ref))
        self.stdout.write("")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run — nada enviado."))
            return

        destino = AniversarioService.destino()
        if not destino:
            raise CommandError(
                "NOTIFICACAO_ANIVERSARIO_DESTINO não configurado — defina o número que recebe o aviso."
            )

        resultado = AniversarioService.notificar(ref, forcar=True)
        if resultado["enviado"]:
            self.stdout.write(self.style.SUCCESS(f"Enviado para {destino[:6]}***."))
        else:
            self.stdout.write(self.style.ERROR(f"Não enviado (motivo: {resultado['motivo']})."))
