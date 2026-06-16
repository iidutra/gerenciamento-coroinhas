from django.core.management.base import BaseCommand
from django_redis import get_redis_connection


class Command(BaseCommand):
    help = "Remove chaves de rate limit de login/recuperação de senha no Redis."

    def handle(self, *args, **options):
        conn = get_redis_connection("default")
        deleted = 0
        for key in conn.scan_iter("*auth:*"):
            conn.delete(key)
            deleted += 1
        self.stdout.write(self.style.SUCCESS(f"Removidas {deleted} chave(s) auth:*"))
