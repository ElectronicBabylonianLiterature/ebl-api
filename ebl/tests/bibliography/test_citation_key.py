from ebl.bibliography.application.citation_key import (
    generate_citation_key,
    unique_citation_key,
)


def test_generate_citation_key_from_author_year_title() -> None:
    assert (
        generate_citation_key(
            {
                "author": [{"family": "George", "given": "Andrew"}],
                "issued": {"date-parts": [[2003]]},
                "title": "The Gilgamesh Epic",
            }
        )
        == "george2003Gilgamesh"
    )


def test_generate_citation_key_uses_editor_when_author_missing() -> None:
    assert (
        generate_citation_key(
            {
                "editor": [{"family": "Frahm"}],
                "issued": {"date-parts": [[2011]]},
                "title": "Babylonian Literature",
            }
        )
        == "frahm2011Babylonian"
    )


def test_generate_citation_key_handles_missing_fields() -> None:
    assert generate_citation_key({}) == "anonnduntitled"


def test_generate_citation_key_normalizes_punctuation_and_diacritics() -> None:
    assert (
        generate_citation_key(
            {
                "author": [{"family": "Geller-Smith"}],
                "issued": {"date-parts": [[1997]]},
                "title": "L'épopée de Gilgameš!",
            }
        )
        == "gellerSmith1997Epopee"
    )


def test_unique_citation_key_adds_collision_suffix() -> None:
    entry = {
        "author": [{"family": "George"}],
        "issued": {"date-parts": [[2003]]},
        "title": "The Gilgamesh Epic",
    }

    assert unique_citation_key(
        entry, {"george2003Gilgamesh", "george2003Gilgamesh-2"}
    ) == ("george2003Gilgamesh-3")
