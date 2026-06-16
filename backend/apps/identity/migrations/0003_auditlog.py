# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "acao",
                    models.CharField(
                        choices=[
                            ("login_sucesso", "Login bem-sucedido"),
                            ("login_falha", "Tentativa de login falhou"),
                            ("recuperar_senha", "Recuperação de senha"),
                            ("recuperar_senha_falha", "Recuperação de senha falhou"),
                            ("presenca_registrada", "Presença registrada"),
                            ("inscricao_criada", "Inscrição pública criada"),
                            ("inscricao_aprovada", "Inscrição aprovada"),
                            ("inscricao_rejeitada", "Inscrição rejeitada"),
                            ("mensagem_enviada", "Mensagem enviada"),
                        ],
                        db_index=True,
                        max_length=40,
                    ),
                ),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("detalhes", models.JSONField(blank=True, default=dict)),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de auditoria",
                "verbose_name_plural": "Registros de auditoria",
                "ordering": ["-criado_em"],
            },
        ),
    ]
