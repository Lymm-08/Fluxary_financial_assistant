import importlib
import logging

import pytest


def test_telegram_conflict_exits_after_retries_and_explains_resolution(
    monkeypatch, caplog,
):
    monkeypatch.setenv('BOT_TOKEN', 'token-ficticio')
    monkeypatch.setenv('DB_URI', 'sqlite:///:memory:')

    from src.models import db as db_module
    from src.models import migrate as migrate_module

    monkeypatch.setattr(
        db_module,
        'init_db',
        lambda _uri: {'engine': object()},
    )
    monkeypatch.setattr(migrate_module, 'migrate_db', lambda _engine: True)
    main_module = importlib.import_module('main')

    class FakeApplication:
        calls = 0

        def run_polling(self, **_kwargs):
            self.calls += 1
            raise main_module.Conflict('conflito simulado')

    class FakeBuilder:
        def token(self, _token):
            return self

        def build(self):
            return app

    app = FakeApplication()
    monkeypatch.setattr(
        main_module.Application,
        'builder',
        lambda: FakeBuilder(),
    )
    monkeypatch.setattr(main_module, 'register_commands', lambda *_args: None)
    monkeypatch.setattr(main_module.time, 'sleep', lambda _seconds: None)
    caplog.set_level(logging.WARNING)

    with pytest.raises(SystemExit) as exit_error:
        main_module.main()

    assert exit_error.value.code == 1
    assert app.calls == 3
    assert 'Feche a outra instância do bot' in caplog.text
