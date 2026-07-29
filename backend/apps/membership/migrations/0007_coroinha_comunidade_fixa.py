from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0006_coroinha_gemeo_de"),
    ]

    operations = [
        migrations.AddField(
            model_name="coroinha",
            name="comunidade_fixa",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Santuário (escala rotativa)"),
                    ("SantaTerezinha", "Santa Terezinha"),
                    ("NossaSenhoraAuxiliadora", "Nossa Senhora Auxiliadora"),
                ],
                default="",
                help_text="Coroinhas de comunidade não entram na geração automática de grupos.",
                max_length=40,
                verbose_name="Comunidade fixa",
            ),
        ),
    ]
