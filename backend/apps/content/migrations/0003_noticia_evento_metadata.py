from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0002_noticia_destaque_documento_categoria"),
    ]

    operations = [
        migrations.AddField(
            model_name="noticia",
            name="data_evento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="noticia",
            name="data_evento_fim",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="noticia",
            name="horario_evento",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="noticia",
            name="local_evento",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="noticia",
            name="referencia_calendario",
            field=models.CharField(
                blank=True,
                help_text="ID estável para importação do calendário paroquial.",
                max_length=80,
                null=True,
                unique=True,
            ),
        ),
    ]
