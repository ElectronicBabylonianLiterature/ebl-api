import pytest

from scripts.maps.map_polygon_identity import build_polygon_id, slugify


@pytest.mark.parametrize(
    "name,expected",
    [
        ("ekal mašarti (Fort Shalmaneser)", "ekal-masarti-fort-shalmaneser"),
        ("楔", "u6954"),
    ],
)
def test_polygon_slugs_preserve_decomposed_letters_and_safe_fallback(
    name: str, expected: str
) -> None:
    assert slugify(name) == expected


def test_polygon_identity_rejects_control_characters_before_geometry() -> None:
    with pytest.raises(ValueError, match="control character"):
        build_polygon_id("assur", "Area\x00", ())
