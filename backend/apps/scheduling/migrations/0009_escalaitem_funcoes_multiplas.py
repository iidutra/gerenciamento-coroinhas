from django.db import migrations, models


def copiar_funcao_para_lista(apps, schema_editor):
    EscalaItem = apps.get_model("scheduling", "EscalaItem")
    for item in EscalaItem.objects.exclude(funcao__isnull=True).exclude(funcao=""):
        item.funcoes = [item.funcao]
        item.save(update_fields=["funcoes"])


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling", "0008_assessor_multiplo"),
    ]

    operations = [
        migrations.AddField(
            model_name="escalaitem",
            name="funcoes",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(copiar_funcao_para_lista, migrations.RunPython.noop),
    ]