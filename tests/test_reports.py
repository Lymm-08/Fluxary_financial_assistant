from datetime import datetime, timedelta
from types import SimpleNamespace

from src.services import reports
from src.utils.formatter import format_money


def test_category_totals_and_currency_formatting():
    entries = [
        SimpleNamespace(type='receita', amount=150.0, category='Salário'),
        SimpleNamespace(type='despesa', amount=35.5, category='Alimentação'),
        SimpleNamespace(type='despesa', amount=14.5, category='Alimentação'),
    ]

    receitas, despesas, categorias = reports._calcular_totais_e_categorias(entries)

    assert receitas == 150.0
    assert despesas == 50.0
    assert categorias['Alimentação'] == {
        'receitas': 0,
        'despesas': 50.0,
        'count': 2,
    }
    assert reports._formatar_economia_text(receitas, despesas) == 'R$ 100,00 (66.7%)'
    assert reports._formatar_categorias_text(categorias) == (
        '📂 Alimentação: R$ -50,00 (2 transações)\n'
        '📂 Salário: R$ 150,00 (1 transações)\n'
    )
    assert format_money(1234.5) == 'R$ 1.234,50'


def test_detailed_monthly_report_formats_category_totals(db, monkeypatch):
    now = datetime(2025, 6, 15, 12, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(reports, 'datetime', FixedDateTime)
    session = db['Session']()
    session.add_all([
        db['Entry'](
            user_id='42', type='receita', amount=150, category='Salário',
            description='salário', date=now - timedelta(days=2),
        ),
        db['Entry'](
            user_id='42', type='despesa', amount=35.5, category='Alimentação',
            description='almoço', date=now - timedelta(days=1),
        ),
        db['Entry'](
            user_id='42', type='despesa', amount=14.5, category='Alimentação',
            description='café', date=now,
        ),
    ])
    session.add(db['Bank'](user_id='42', total_balance=100))
    session.commit()
    session.close()

    report = reports.generate_report('42', 'completo', db)
    month_report = reports.generate_month_specific_report('42', 6, db)

    assert 'Receitas do Mês: R$ 150,00' in report
    assert 'Despesas do Mês: R$ 50,00' in report
    assert '📂 Alimentação: R$ -50,00 (2 transações)' in report
    assert '📂 Salário: R$ 150,00 (1 transações)' in month_report
    assert 'Total de Transações: 3' in month_report


def test_weekly_and_monthly_reports_filter_and_sum_dates(db, monkeypatch):
    now = datetime(2025, 6, 15, 12, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(reports, 'datetime', FixedDateTime)
    session = db['Session']()
    session.add_all([
        db['Entry'](
            user_id='42', type='despesa', amount=30, category='Alimentação',
            description='jantar recente', date=now - timedelta(days=6),
        ),
        db['Entry'](
            user_id='42', type='receita', amount=200, category='Renda',
            description='salário', date=now - timedelta(days=20),
        ),
        db['Entry'](
            user_id='42', type='despesa', amount=500, category='Compras',
            description='fora do período', date=now - timedelta(days=31),
        ),
    ])
    session.commit()
    session.close()

    weekly = reports.generate_report('42', 'semanal', db)
    monthly = reports.generate_report('42', 'mensal', db)

    assert 'Total: R$ -30,00' in weekly
    assert 'Transações neste período: 1' in weekly
    assert 'Total: R$ 170,00' in monthly
    assert 'Receitas: R$ 200,00' in monthly
    assert 'Despesas: R$ 30,00' in monthly
    assert 'Transações neste período: 2' in monthly
