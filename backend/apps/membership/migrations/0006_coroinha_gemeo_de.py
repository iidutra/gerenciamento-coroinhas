from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0005_coroinha_antigo"),
    ]

    operations = [
        migrations.AddField(
            model_name="coroinha",
            name="gemeo_de",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="gemeos_vinculados",
                to="membership.coroinha",
                verbose_name="Gêmeo de",
            ),
        ),
    ]
