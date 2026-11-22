from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling", "0007_entre_os_dois_duplo"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="escalaitem",
            name="escala_funcao_unica_exceto_entre_os_dois",
        ),
        migrations.AddConstraint(
            model_name="escalaitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(("funcao__isnull", False))
                & ~models.Q(("funcao__in", ["EntreOsDois", "Assessor"])),
                fields=("escala", "funcao"),
                name="escala_funcao_unica_exceto_multiplas",
            ),
        ),
    ]