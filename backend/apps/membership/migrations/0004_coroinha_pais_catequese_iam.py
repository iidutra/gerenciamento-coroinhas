from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0003_configuracao_paroquial"),
    ]

    operations = [
        migrations.AddField(
            model_name="coroinha",
            name="nome_pai",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="coroinha",
            name="telefone_pai",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="coroinha",
            name="nome_mae",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="coroinha",
            name="telefone_mae",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="coroinha",
            name="faz_catequese",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="coroinha",
            name="etapa_catequese",
            field=models.CharField(
                blank=True,
                choices=[
                    ("PreEucaristia", "Pré-Eucaristia"),
                    ("PrimeiraEucaristia", "Primeira Eucaristia"),
                    ("Crisma", "Crisma"),
                ],
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="coroinha",
            name="faz_iam",
            field=models.BooleanField(default=False),
        ),
    ]
