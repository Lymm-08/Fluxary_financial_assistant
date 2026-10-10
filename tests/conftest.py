import pytest

from src.models.db import Bank, Entry, init_db


@pytest.fixture
def db():
    database = init_db('sqlite:///:memory:')
    yield {
        **database,
        'Entry': Entry,
        'Bank': Bank,
    }
    database['engine'].dispose()
