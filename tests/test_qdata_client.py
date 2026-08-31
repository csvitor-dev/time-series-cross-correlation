import json

import httpx
import respx
from conftest import FIXTURES

from acquisition.qdata_client import QDataHTTPSource
from config import QDataSettings
from contracts.ohlc import OHLCRequest

SETTINGS = QDataSettings(
    auth_url="https://auth.test", http_url="https://http.test", username="u", password="p"
)


@respx.mock
def test_authenticates_then_fetches_and_maps_camelcase():
    items = json.loads((FIXTURES / "ohlc_winj26_sample.json").read_text())
    auth = respx.post("https://auth.test/api/v1/auth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "token_type": "bearer"})
    )
    ohlc = respx.get("https://http.test/api/v1/distribution/ohlc").mock(
        return_value=httpx.Response(200, json=items)
    )

    source = QDataHTTPSource(SETTINGS, httpx.Client())
    bars = source.fetch_ohlc(
        OHLCRequest(symbol="WINJ26", timeframe="M1", start_time=0, end_time=9_999_999_999)
    )

    assert auth.called
    request = ohlc.calls.last.request
    assert request.headers["authorization"] == "Bearer tok"
    assert dict(request.url.params)["symbol"] == "WINJ26"
    assert dict(request.url.params)["order_desc"] == "true"
    assert [b.tick_volume for b in bars] == [i["tickVolume"] for i in items]
