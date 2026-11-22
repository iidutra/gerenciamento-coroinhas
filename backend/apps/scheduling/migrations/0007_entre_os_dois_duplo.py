from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling", "0006_alter_missa_options"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="escalaitem",
            name="escala_funcao_unica",
        ),
        migrations.AddConstraint(
            model_name="escalaitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(("funcao__isnull", False))
                & ~models.Q(("funcao", "EntreOsDois")),
                fields=("escala", "funcao"),
                name="escala_funcao_unica_exceto_entre_os_dois",
            ),
        ),
    ]