import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("scheduling", "0004_vela1_vela2"),
    ]

    operations = [
        migrations.AddField(
            model_name="missa",
            name="local",
            field=models.CharField(
                choices=[
                    ("Santuario", "Santuário de Fátima"),
                    ("Comunidade", "Comunidade Santo Antônio"),
                ],
                default="Santuario",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="missa",
            name="tipo_slot",
            field=models.CharField(
                choices=[
                    ("SabadoNoite", "Sábado noite"),
                    ("DomingoManha", "Domingo manhã"),
                    ("DomingoNoite", "Domingo noite"),
                    ("SextaAdoracao", "Sexta — Adoração + Missa"),
                    ("QuartaVoluntarios", "Quarta — Voluntários"),
                    ("Dia13", "Dia 13"),
                    ("ComunidadeDomingo", "Comunidade — Domingo"),
                    ("Outro", "Outro"),
                ],
                default="Outro",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="escala",
            name="modo",
            field=models.CharField(
                choices=[
                    ("SorteioAutomatico", "Sorteio automático"),
                    ("SelecaoManual", "Seleção manual"),
                    ("GrupoMensal", "Grupo mensal"),
                ],
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="EscalaMensal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ano", models.PositiveSmallIntegerField()),
                ("mes", models.PositiveSmallIntegerField()),
                ("tamanho_grupo", models.PositiveSmallIntegerField(default=9)),
                ("quantidade_sexta", models.PositiveSmallIntegerField(default=2)),
                ("quantidade_comunidade", models.PositiveSmallIntegerField(default=2)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "criado_por",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="escalas_mensais_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Escala mensal",
                "verbose_name_plural": "Escalas mensais",
                "ordering": ["-ano", "-mes"],
                "unique_together": {("ano", "mes")},
            },
        ),
        migrations.AddField(
            model_name="escala",
            name="escala_mensal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="escalas",
                to="scheduling.escalamensal",
            ),
        ),
        migrations.AddField(
            model_name="escala",
            name="grupo_numero",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="escala",
            name="observacao",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="escala",
            name="voluntarios",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="GrupoMensal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero", models.PositiveSmallIntegerField()),
                (
                    "escala_mensal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grupos",
                        to="scheduling.escalamensal",
                    ),
                ),
            ],
            options={
                "ordering": ["numero"],
                "unique_together": {("escala_mensal", "numero")},
            },
        ),
        migrations.CreateModel(
            name="GrupoMensalMembro",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                (
                    "coroinha",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grupos_mensais",
                        to="membership.coroinha",
                    ),
                ),
                (
                    "grupo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="membros",
                        to="scheduling.grupomensal",
                    ),
                ),
            ],
            options={
                "ordering": ["ordem"],
                "unique_together": {("grupo", "coroinha")},
            },
        ),
    ]
