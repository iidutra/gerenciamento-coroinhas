import pytest

from apps.communication.utils.nome import primeiro_nome


@pytest.mark.parametrize(
    "completo,esperado",
    [
        ("Thiago Silva", "Thiago"),
        ("Maria Eduarda de Souza", "Maria Eduarda"),
        ("Ana Cecília de Souza Furtado Frias", "Ana Cecília"),
        ("Maria de Lourdes", "Maria"),
        ("João Pedro Alves", "João Pedro"),
        ("José Carlos", "José Carlos"),
        ("Pedro", "Pedro"),
        ("", ""),
        ("  Luiz   Felipe  Santos ", "Luiz Felipe"),
    ],
)
def test_primeiro_nome(completo, esperado):
    assert primeiro_nome(completo) == esperado


@pytest.mark.django_db
def test_render_mensagem_usa_primeiro_nome():
    from datetime import date

    from apps.communication.services.comunicacao_service import ComunicacaoService
    from apps.membership.models import Coroinha

    coroinha = Coroinha.objects.create(
        nome="Maria Eduarda de Souza",
        data_nascimento=date(2014, 1, 1),
    )
    texto = ComunicacaoService.preview("Olá {nome}!", coroinha.id)
    assert texto == "Olá Maria Eduarda!"
