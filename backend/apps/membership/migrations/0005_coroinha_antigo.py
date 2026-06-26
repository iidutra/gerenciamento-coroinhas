from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0004_coroinha_pais_catequese_iam"),
    ]

    operations = [
        migrations.AddField(
            model_name="coroinha",
            name="antigo",
            field=models.BooleanField(default=False),
        ),
    ]
