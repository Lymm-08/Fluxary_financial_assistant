import requests
import pytest

from src.ai import categorizer


class FakeResponse:
    ok = True
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def test_categorize_uses_hugging_face_response(monkeypatch):
    response = FakeResponse([{'generated_text': 'Categoria: Alimentação'}])
    monkeypatch.setattr(
        categorizer.requests,
        'post',
        lambda *args, **kwargs: response,
    )
    monkeypatch.setattr(categorizer, 'HF_TOKEN', 'token-de-teste')

    assert categorizer.categorize('pizza no jantar') == 'Alimentação'


def test_api_timeout_uses_keyword_fallback(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout('timeout de teste')

    monkeypatch.setattr(categorizer.requests, 'post', timeout)
    monkeypatch.setattr(categorizer.time, 'sleep', lambda *_: None)

    assert categorizer.categorize('corrida de uber') == 'Transporte'


@pytest.mark.parametrize('payload', [[], [{}], {'unexpected': 'format'}])
def test_invalid_api_response_uses_fallback(monkeypatch, payload):
    calls = []

    def post(*args, **kwargs):
        calls.append(kwargs)
        return FakeResponse(payload)

    monkeypatch.setattr(categorizer.requests, 'post', post)
    monkeypatch.setattr(categorizer.time, 'sleep', lambda *_: None)

    assert categorizer.categorize('corrida de uber') == 'Transporte'
    assert len(calls) == 3
