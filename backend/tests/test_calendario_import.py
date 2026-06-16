import pytest
from django.core.management import call_command
from rest_framework import status

from apps.content.models import Noticia
from apps.training.models import Formacao

pytestmark = pytest.mark.django_db


class TestImportarCalendario:
    def test_importacao_cria_noticias_e_formacoes(self):
        call_command("importar_calendario_paroquial", sem_missas=True)
        assert Noticia.objects.filter(referencia_calendario__isnull=False).count() >= 1
        assert Formacao.objects.count() >= 1

    def test_importacao_idempotente(self):
        call_command("importar_calendario_paroquial", sem_missas=True)
        total = Noticia.objects.filter(referencia_calendario__isnull=False).count()
        call_command("importar_calendario_paroquial", sem_missas=True)
        assert Noticia.objects.filter(referencia_calendario__isnull=False).count() == total

    def test_noticia_sem_tag_tecnica(self):
        call_command("importar_calendario_paroquial", sem_missas=True)
        noticia = Noticia.objects.filter(referencia_calendario="missa-fatima-mar").first()
        assert noticia is not None
        assert "[calendario-paroquial]" not in noticia.conteudo
        assert noticia.data_evento is not None
        assert noticia.local_evento
