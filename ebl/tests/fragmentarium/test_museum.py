import pytest

from ebl.fragmentarium.domain.museum import Museum


@pytest.mark.parametrize(
    "key,museum_name,city,country,url",
    [
        (
            "BIRMINGHAM_MUSEUM_AND_ART_GALLERY",
            "Birmingham Museum and Art Gallery",
            "Birmingham",
            "GB",
            "https://www.birminghammuseums.org.uk/",
        ),
        (
            "WORLD_MUSEUM_LIVERPOOL",
            "World Museum",
            "Liverpool",
            "GB",
            "https://www.liverpoolmuseums.org.uk/world-museum",
        ),
    ],
)
def test_museum_entry(key, museum_name, city, country, url) -> None:
    museum = Museum[key]

    assert museum.name == key
    assert museum.museum_name == museum_name
    assert museum.city == city
    assert museum.country == country
    assert museum.url == url
