from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling", "0009_escalaitem_funcoes_multiplas"),
    ]

    operations = [
        migrations.AddField(
            model_name="escala",
            name="todos_coroinhas",
            field=models.BooleanField(
                default=False,
                help_text="Todos os coroinhas elegíveis participam; funções litúrgicas aparecem em destaque.",
            ),
        ),
    ]