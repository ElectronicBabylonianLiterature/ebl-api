import httpretty
import pytest

import ebl.cdli.infrastructure.cdli_client as client

CDLI_NUMBER = "P397611"
METHODS = [
    (client.get_photo_url, f"https://cdli.mpiwg-berlin.mpg.de/dl/photo/{CDLI_NUMBER}.jpg"),
    (client.get_line_art_url, f"https://cdli.mpiwg-berlin.mpg.de/dl/lineart/{CDLI_NUMBER}_l.jpg"),
    (
        client.get_detail_line_art_url,
        f"https://cdli.mpiwg-berlin.mpg.de/dl/lineart/{CDLI_NUMBER}_ld.jpg",
    ),
]
STATUSES = {200: True, 404: False, 503: False}


@pytest.mark.parametrize("method,url", METHODS)
@pytest.mark.parametrize("status", STATUSES.keys())
@httpretty.activate
def test_getting_url(method, url, status):
    httpretty.register_uri(httpretty.HEAD, url, status=status)
    result = method(CDLI_NUMBER)

    assert result == (url if STATUSES[status] else None)
