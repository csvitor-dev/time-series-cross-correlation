from __future__ import annotations

import httpx

from config import QDataSettings
from contracts.auth import Credentials, TokenResponse
from contracts.market_data_source import MarketDataSource
from contracts.ohlc import OHLCBar, OHLCRequest

_AUTH_ROUTE = "/api/v1/auth/token"
_OHLC_ROUTE = "/api/v1/distribution/ohlc"


class QDataHTTPSource(MarketDataSource):
    def __init__(self, settings: QDataSettings | None = None, client: httpx.Client | None = None):
        self._settings = settings or QDataSettings()
        self._client = client or httpx.Client(timeout=30.0)
        self._token: str | None = None

    def authenticate(self) -> TokenResponse:
        creds = Credentials(
            username=self._settings.username, password=self._settings.password
        )
        response = self._client.post(
            f"{self._settings.auth_url}{_AUTH_ROUTE}", json=creds.model_dump()
        )
        response.raise_for_status()
        token = TokenResponse.model_validate(response.json())
        self._token = token.access_token
        return token

    def fetch_ohlc(self, request: OHLCRequest) -> list[OHLCBar]:
        if self._token is None:
            self.authenticate()

        bars: list[OHLCBar] = []
        offset = request.offset
        while True:
            page = request.model_copy(update={"offset": offset})
            response = self._client.get(
                f"{self._settings.http_url}{_OHLC_ROUTE}",
                params=page.as_query(),
                headers={"Authorization": f"Bearer {self._token}"},
            )
            response.raise_for_status()
            items = response.json() or []
            bars.extend(OHLCBar.model_validate(item) for item in items)
            if len(items) < request.limit:
                break
            offset += request.limit

        bars.sort(key=lambda bar: bar.time)
        return bars
