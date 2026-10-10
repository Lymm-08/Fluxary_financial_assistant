import asyncio
from types import SimpleNamespace

import pytest

from src.commands import handlers


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


@pytest.mark.parametrize(
    ('text', 'category', 'expected_type', 'expected_amount', 'expected_balance'),
    [
        ('recebi 1.250,50 salario', 'Renda', 'receita', 1250.50, 1250.50),
        ('paguei 34,90 pizza', 'Alimentação', 'despesa', 34.9, -34.9),
    ],
)
def test_handle_message_records_income_and_expense(
    db, monkeypatch, text, category, expected_type, expected_amount,
    expected_balance,
):
    monkeypatch.setattr(handlers, 'categorize', lambda _description: category)
    message = FakeMessage(text)
    update = SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=42),
    )
    context = SimpleNamespace(user_data={})

    asyncio.run(handlers.handle_message(update, context, db))

    session = db['Session']()
    entry = session.query(db['Entry']).one()
    bank = session.query(db['Bank']).one()
    assert entry.user_id == '42'
    assert entry.type == expected_type
    assert entry.amount == expected_amount
    assert bank.total_balance == expected_balance
    assert 'Registrado com sucesso' in message.replies[0]
    session.close()


def test_handle_message_replies_to_invalid_input(db):
    message = FakeMessage('nenhum valor informado')
    update = SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=42),
    )
    context = SimpleNamespace(user_data={})

    asyncio.run(handlers.handle_message(update, context, db))

    assert 'Não consegui processar sua mensagem' in message.replies[0]
    session = db['Session']()
    assert session.query(db['Entry']).count() == 0
    session.close()
