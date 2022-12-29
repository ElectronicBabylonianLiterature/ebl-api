import falcon
import httpretty
import pytest


STATUSES = {200: True, 404: False}


@pytest.mark.parametrize("photo_status", STATUSES.keys())
@pytest.mark.parametrize("line_art_status", STATUSES.keys())
@pytest.mark.parametrize("detail_line_art_status", STATUSES.keys())
@httpretty.activate
def test_get(photo_status, line_art_status, detail_line_art_status, client):
    cdli_number = "P397611"
    photo_url = f"https://cdli.mpiwg-berlin.mpg.de/dl/photo/{cdli_number}.jpg"
    line_art_url = f"https://cdli.mpiwg-berlin.mpg.de/dl/lineart/{cdli_number}_l.jpg"
    detail_line_art_url = (
        f"https://cdli.mpiwg-berlin.mpg.de/dl/lineart/{cdli_number}_ld.jpg"
    )

    httpretty.register_uri(httpretty.HEAD, photo_url, status=photo_status)
    httpretty.register_uri(httpretty.HEAD, line_art_url, status=line_art_status)
    httpretty.register_uri(
        httpretty.HEAD, detail_line_art_url, status=detail_line_art_status
    )
    result = client.simulate_get(f"/cdli/{cdli_number}")

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "photoUrl": photo_url if STATUSES[photo_status] else None,
        "lineArtUrl": line_art_url if STATUSES[line_art_status] else None,
        "detailLineArtUrl": (
            detail_line_art_url if STATUSES[detail_line_art_status] else None
        ),
    }
