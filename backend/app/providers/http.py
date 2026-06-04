import json
from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.providers.interfaces import ProviderTransportError


class JsonHttpClient(Protocol):
    def get_json(self, url: str) -> dict[str, object]: ...


class UrlLibJsonHttpClient:
    def get_json(self, url: str) -> dict[str, object]:
        request = Request(url, headers={"User-Agent": "trendwise-prototype/0.1"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProviderTransportError(str(error)) from error

        if not isinstance(payload, dict):
            raise ProviderTransportError("Provider returned non-object JSON")
        return payload
