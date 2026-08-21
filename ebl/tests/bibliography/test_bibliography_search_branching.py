"""`Bibliography.search` must not query by author/year/title when the query
does not parse as one. Asserted by verifying the repository method is never
called -- not by asserting on final output, since the fixture's stubbed
repository would return the same result whether or not the guard ran.
"""

from mockito import ANY, verify

from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_search_skips_the_author_query_when_it_does_not_parse(
    bibliography, bibliography_repository, when
):
    entry = BibliographyEntryFactory.build(id="Q1", container_title_short="123")
    (
        when(bibliography_repository)
        .query_by_container_title_and_collection_number("123", None)
        .thenReturn([entry])
    )
    (
        when(bibliography_repository)
        .query_by_title_short_and_volume("123", None)
        .thenReturn([])
    )

    assert bibliography.search("123") == [entry]
    verify(bibliography_repository, times=0).query_by_author_year_and_title(
        ANY, ANY, ANY
    )
