from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Cria bucket MinIO quando USE_MINIO está ativo."

    def handle(self, *args, **options):
        if not getattr(settings, "USE_MINIO", False):
            self.stdout.write("USE_MINIO desligado — nada a fazer.")
            return

        import boto3
        from botocore.exceptions import ClientError

        bucket = settings.AWS_STORAGE_BUCKET_NAME
        client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="us-east-1",
        )
        try:
            client.head_bucket(Bucket=bucket)
            self.stdout.write(f"Bucket '{bucket}' já existe.")
        except ClientError:
            client.create_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket}' criado."))
