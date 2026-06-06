import pytest

from app.providers.http import UrlLibJsonHttpClient
from app.providers.interfaces import ProviderTransportError


class FakeResponse:
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return b"\xff"


def test_url_lib_json_http_client_wraps_unicode_decode_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr("app.providers.http.urlopen", fake_urlopen)

    with pytest.raises(ProviderTransportError):
        UrlLibJsonHttpClient().get_json("https://example.test/bad-json")
