import pytest

from src.utils.parser import parse_transaction_message


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('30,90 pizza', (30.90, 'pizza')),
        ('pizza 30.90', (30.90, 'pizza')),
        ('recebi 1.250,50 salario', (1250.50, 'recebi salario')),
        ('R$ 45,00 almoço', (45.0, 'almoço')),
        ('paguei 22,50 no mercado', (22.5, 'paguei no mercado')),
    ],
)
def test_parse_transaction_message(text, expected):
    assert parse_transaction_message(text) == expected


@pytest.mark.parametrize('text', ['sem valor', '100', ''])
def test_parse_transaction_message_requires_description(text):
    assert parse_transaction_message(text) is None
