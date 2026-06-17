from ebl.bibliography.application.duplicate_audit import (
    UsageCounts,
    cluster_pairs,
    generate_candidate_pairs,
    metadata_completeness,
    normalize_doi,
    normalize_entry,
    normalize_isbn,
    normalize_issn,
    normalize_text,
    reviewed_not_duplicate_pairs,
    score_pair,
    suggest_canonical,
)


def entry(id_, **overrides):
    data = {
        "_id": id_,
        "type": "book",
        "title": "The Gilgamesh Epic",
        "author": [{"family": "George", "given": "Andrew"}],
        "issued": {"date-parts": [[2003]]},
        "publisher": "Oxford University Press",
    }
    data.update(overrides)
    return data


def test_normalize_doi() -> None:
    assert normalize_doi(" DOI: https://doi.org/10.123/ABC ") == "10.123/abc"
    assert normalize_doi("http://dx.doi.org/10.1000/X") == "10.1000/x"
    assert normalize_doi("") == ""
    assert normalize_doi("<>") == ""
    assert normalize_doi("pending") == ""


def test_normalize_isbn() -> None:
    assert normalize_isbn("978-0-19-927841-1") == "9780199278411"
    assert normalize_isbn("0 306 40615 X") == "030640615X"


def test_normalize_issn() -> None:
    assert normalize_issn("1234-567X") == "1234567X"


def test_normalize_title() -> None:
    assert normalize_text("L'épopée   de Gilgameš!") == "l epopee de gilgames"


def test_contributor_and_year_normalization() -> None:
    normalized = normalize_entry(entry("A"))
    assert normalized.contributors == ("george|a",)
    assert normalized.primary_family == "george"
    assert normalized.year == 2003


def test_exact_doi_duplicate_is_likely() -> None:
    left = normalize_entry(entry("A", DOI="10.123/ABC"))
    right = normalize_entry(entry("B", DOI="https://doi.org/10.123/abc"))
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.score >= 0.97
    assert score.matched_signals["doi"] == 1.0


def test_exact_doi_with_conflict_still_needs_review() -> None:
    left = normalize_entry(entry("A", DOI="10.123/ABC"))
    right = normalize_entry(
        entry("B", DOI="10.123/abc", issued={"date-parts": [[1999]]})
    )
    score = score_pair(left, right)
    assert score.decision == "possible_duplicate"
    assert score.score >= 0.76
    assert score.matched_signals["doi"] == 1.0
    assert "year" in score.conflicting_signals


def test_exact_doi_with_strong_metadata_conflict_flags_data_issue() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="On Gilgamesh",
            author=[{"family": "George", "given": "Andrew"}],
            issued={"date-parts": [[2003]]},
            DOI="10.123/abc",
            page="1-10",
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="A Study of Astronomical Diaries",
            author=[{"family": "Rochberg", "given": "Francesca"}],
            issued={"date-parts": [[1991]]},
            DOI="10.123/abc",
            page="44-60",
        )
    )
    score = score_pair(left, right)
    assert score.decision == "possible_duplicate"
    assert score.matched_signals["doi"] == 1.0
    assert "doi_data_issue" in score.conflicting_signals


def test_exact_isbn_duplicate_is_likely_with_compatible_title() -> None:
    left = normalize_entry(entry("A", ISBN="978-0-19-927841-1"))
    right = normalize_entry(
        entry("B", title="The Gilgamesh Epic.", ISBN="9780199278411")
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.matched_signals["isbn"] == 1.0


def test_exact_isbn_duplicate_is_likely_with_compatible_volume() -> None:
    left = normalize_entry(
        entry(
            "A", title="Royal Inscriptions Volume 1", volume="1", ISBN="9780199278411"
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="Royal Inscriptions Volume I",
            volume="1",
            ISBN="978-0-19-927841-1",
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.matched_signals["isbn"] == 1.0


def test_book_series_part_siblings_are_not_likely_duplicates() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="Cuneiform Texts Part I",
            **{"collection-title": "Cuneiform Texts", "volume": "1"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="Cuneiform Texts Part II",
            **{"collection-title": "Cuneiform Texts", "volume": "2"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "series_part" in score.conflicting_signals


def test_book_series_spelled_part_siblings_are_not_duplicates() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="Babylonian Provincial Officials Part One",
            author=[{"family": "Smith", "given": "Mark"}],
            issued={"date-parts": [[2010]]},
            publisher="Eisenbrauns",
            **{"collection-title": "Babylonian Provincial Officials"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="Babylonian Provincial Officials Part Two",
            author=[{"family": "Smith", "given": "Mark"}],
            issued={"date-parts": [[2010]]},
            publisher="Eisenbrauns",
            **{"collection-title": "Babylonian Provincial Officials"},
        )
    )
    score = score_pair(left, right)
    assert score.decision == "not_duplicate"
    assert "series_part" in score.conflicting_signals


def test_book_series_volume_siblings_are_not_likely_duplicates() -> None:
    left = normalize_entry(entry("A", title="Royal Archives Volume I", volume="1"))
    right = normalize_entry(entry("B", title="Royal Archives Volume II", volume="2"))
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "series_part" in score.conflicting_signals


def test_book_series_teil_siblings_are_not_likely_duplicates() -> None:
    left = normalize_entry(entry("A", title="Urkunden aus Lagasch Teil 1"))
    right = normalize_entry(entry("B", title="Urkunden aus Lagasch Teil 2"))
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "series_part" in score.conflicting_signals


def test_book_series_band_heft_siblings_are_not_likely_duplicates() -> None:
    left = normalize_entry(entry("A", title="Archiv fur Orientforschung Band I Heft 1"))
    right = normalize_entry(
        entry("B", title="Archiv fur Orientforschung Band I Heft 2")
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "series_part" in score.conflicting_signals


def test_encyclopedia_entries_need_high_title_similarity() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="entry-encyclopedia",
            title="Adad",
            **{"container-title": "Reallexikon der Assyriologie", "volume": "1"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="entry-encyclopedia",
            title="Ea",
            **{"container-title": "Reallexikon der Assyriologie", "volume": "1"},
        )
    )
    score = score_pair(left, right)
    assert score.decision == "not_duplicate"
    assert "different_entry_title" in score.conflicting_signals


def test_same_encyclopedia_lemma_remains_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="entry-encyclopedia",
            title="Marduk",
            issued={"date-parts": [[1999]]},
            page="360-370",
            **{"container-title": "Reallexikon der Assyriologie", "volume": "7"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="entry-encyclopedia",
            title="Marduk.",
            issued={"date-parts": [[1999]]},
            page="360-370",
            **{"container-title": "Reallexikon der Assyriologie", "volume": "7"},
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"


def test_article_siblings_with_different_titles_and_pages_are_not_likely() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="First Note on Uruk",
            page="1-10",
            **{"container-title": "NABU", "volume": "12"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="Second Note on Sippar",
            page="11-20",
            **{"container-title": "NABU", "volume": "12"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "different_page" in score.conflicting_signals


def test_same_series_different_books_are_not_likely_duplicates() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="Administrative Documents from Ur",
            author=[{"family": "Jones", "given": "Mary"}],
            issued={"date-parts": [[1971]]},
            publisher="University Museum",
            **{"collection-title": "Babylonian Publications Series"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="Sumerian Literary Catalogues",
            author=[{"family": "Jones", "given": "Mary"}],
            issued={"date-parts": [[1971]]},
            publisher="University Museum",
            **{"collection-title": "Babylonian Publications Series"},
        )
    )
    score = score_pair(left, right)
    assert score.decision == "not_duplicate"
    assert "different_title" in score.conflicting_signals


def test_exact_doi_with_low_title_and_contributor_similarity_is_downgraded() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="Administrative Documents from Nippur",
            author=[{"family": "Jones", "given": "Mary"}],
            issued={"date-parts": [[1971]]},
            DOI="10.5555/copied",
            page="1-50",
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="A Grammar of Old Babylonian Letters",
            author=[{"family": "Black", "given": "Jeremy"}],
            issued={"date-parts": [[2001]]},
            DOI="10.5555/copied",
            page="100-160",
        )
    )
    score = score_pair(left, right)
    assert score.decision == "possible_duplicate"
    assert score.matched_signals["doi"] == 1.0
    assert "doi_data_issue" in score.conflicting_signals
    assert "different_title" in score.conflicting_signals


def test_chapter_collection_siblings_with_different_titles_and_pages_are_not_likely() -> (
    None
):
    left = normalize_entry(
        entry(
            "A",
            type="chapter",
            title="Trade in Babylonia",
            page="1-18",
            **{"container-title": "Studies in Cuneiform Culture", "publisher": "Brill"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="chapter",
            title="Astronomy in Assyria",
            page="19-38",
            **{"container-title": "Studies in Cuneiform Culture", "publisher": "Brill"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "different_page" in score.conflicting_signals


def test_issn_only_is_supporting_not_hard_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="First Article",
            issued={"date-parts": [[2001]]},
            ISSN="1234-5678",
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="Different Article",
            issued={"date-parts": [[2010]]},
            ISSN="12345678",
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert score.score < 0.76
    assert score.matched_signals["issn"] == 1.0


def test_same_author_year_fuzzy_title_is_possible() -> None:
    left = normalize_entry(entry("A", title="The Gilgamesh Epic"))
    right = normalize_entry(entry("B", title="The Gilgamesh Epic: Introduction"))
    score = score_pair(left, right)
    assert score.decision in {"possible_duplicate", "likely_duplicate"}
    contributor_score = score.matched_signals["contributors"]
    assert contributor_score is not None
    assert contributor_score >= 0.9
    assert score.matched_signals["year"] == 1.0


def test_article_container_page_matching_scores() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="A Study of Gilgamesh",
            **{
                "container-title": "Journal of Cuneiform Studies",
                "volume": "12",
                "issue": "1",
                "page": "1-20",
            },
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="A Study of Gilgameš",
            **{
                "container-title": "Journal of Cuneiform Studies",
                "volume": "12",
                "issue": "1",
                "page": "1–20",
            },
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.matched_signals["containerTitle"] == 1.0


def test_title_punctuation_diacritic_case_variants_remain_likely() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="L'epopee de Gilgames",
            page="1-20",
            **{"container-title": "Journal of Cuneiform Studies"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="L'épopée de Gilgameš!",
            page="1-20",
            **{"container-title": "Journal of Cuneiform Studies"},
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"


def test_id_format_variants_with_same_bibliography_remain_likely() -> None:
    left = normalize_entry(
        entry("George.2003", title="The Babylonian Gilgamesh Epic", page="1-20")
    )
    right = normalize_entry(
        entry("George_2003", title="The Babylonian Gilgamesh Epic", page="1-20")
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"


def test_mixed_candidate_group_does_not_pull_weak_related_record_into_likely_group() -> (
    None
):
    normalized_entries = {
        id_: normalize_entry(data)
        for id_, data in {
            "A": entry(
                "A",
                title="The Marduk Prophecy",
                author=[{"family": "Lambert", "given": "Wilfred"}],
                issued={"date-parts": [[1998]]},
                page="1-20",
                **{"container-title": "Journal of Ancient Near Eastern Studies"},
            ),
            "B": entry(
                "B",
                title="The Marduk Prophecy.",
                author=[{"family": "Lambert", "given": "Wilfred"}],
                issued={"date-parts": [[1998]]},
                page="1-20",
                **{"container-title": "Journal of Ancient Near Eastern Studies"},
            ),
            "C": entry(
                "C",
                title="Notes on Marduk Theology",
                author=[{"family": "Lambert", "given": "Wilfred"}],
                issued={"date-parts": [[1998]]},
                page="21-42",
                **{"container-title": "Journal of Ancient Near Eastern Studies"},
            ),
        }.items()
    }
    pairs = [
        score_pair(normalized_entries["A"], normalized_entries["B"]),
        score_pair(normalized_entries["A"], normalized_entries["C"]),
    ]
    groups = cluster_pairs(pairs, normalized_entries)

    likely_groups = [
        group for group in groups if group.group_decision == "likely_duplicate"
    ]
    assert likely_groups[0].member_ids == ["A", "B"]


def test_book_edition_variation_creates_conflict() -> None:
    left = normalize_entry(entry("A", edition="1"))
    right = normalize_entry(entry("B", edition="2"))
    score = score_pair(left, right)
    assert "edition" in score.conflicting_signals


def test_missing_author_year_title_is_insufficient() -> None:
    left = normalize_entry({"_id": "A", "type": "book", "ISSN": "1234-5678"})
    right = normalize_entry({"_id": "B", "type": "book", "ISSN": "12345678"})
    score = score_pair(left, right)
    assert score.decision == "insufficient_data"


def test_generate_candidate_pairs_honors_false_positive_override() -> None:
    entries = [
        normalize_entry(entry("A", DOI="10.1/a")),
        normalize_entry(entry("B", DOI="10.1/a")),
    ]
    pairs = generate_candidate_pairs(entries, {("A", "B")})
    assert pairs[0].previously_reviewed_not_duplicate is True
    assert pairs[0].decision == "not_duplicate"


def test_duplicate_group_clustering_connects_transitive_pairs() -> None:
    normalized_entries = {
        id_: normalize_entry(entry(id_, title=title))
        for id_, title in {
            "A": "The Gilgamesh Epic",
            "B": "The Gilgamesh Epic Introduction",
            "C": "Gilgamesh Epic Introduction",
        }.items()
    }
    pairs = [
        score_pair(normalized_entries["A"], normalized_entries["B"]),
        score_pair(normalized_entries["B"], normalized_entries["C"]),
    ]
    groups = cluster_pairs(pairs, normalized_entries)
    assert len(groups) == 1
    assert groups[0].member_ids == ["A", "B", "C"]


def test_suggest_canonical_prefers_complete_used_identifier_record() -> None:
    sparse = normalize_entry(entry("A", title="", author=[], DOI=""))
    complete = normalize_entry(entry("B", DOI="10.1/b"))
    canonical_id, reason = suggest_canonical(
        [sparse, complete], {"B": UsageCounts(fragments=3)}
    )
    assert canonical_id == "B"
    assert "usage count (3)" in reason
    assert metadata_completeness(complete) > metadata_completeness(sparse)


def test_encyclopedia_distinct_lemmas_are_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="entry-encyclopedia",
            title="Zelt A. I. Philologisch. In Mesopotamien · Tent A. I. Philological. In Mesopotamia",
            issued={"date-parts": [[2017]]},
            **{"container-title": "Reallexikon der Assyriologie", "volume": "15"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="entry-encyclopedia",
            title="Wasser A. I. Philologisch. In Mesopotamien · Water A. I. Philological. In Mesopotamia",
            issued={"date-parts": [[2017]]},
            **{"container-title": "Reallexikon der Assyriologie", "volume": "15"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "different_entry_title" in score.conflicting_signals


def test_doi_title_conflict_is_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="book",
            title="Sumerian Grammatical Texts",
            DOI="10.123/SharedDoi",
            **{
                "collection-title": "PBS",
                "container-title": "PBS",
                "publisher": "University Museum",
            },
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="book",
            title="Sumerian Liturgical Texts",
            DOI="10.123/SharedDoi",
            **{
                "collection-title": "PBS",
                "container-title": "PBS",
                "publisher": "University Museum",
            },
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert score.matched_signals["doi"] == 1.0
    assert "doi_data_issue" in score.conflicting_signals


def test_webpage_stt_siblings_are_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="webpage",
            title="STT 1, 061 [Šu'ila to Šamaš]. (http://oracc.org/cams/gkab/P338379)",
            issued={"date-parts": [[2009]]},
            author=[{"family": "Cunningham", "given": "Graham"}],
            **{"container-title": "CAMS/GKAB"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="webpage",
            title="STT 2, 122 [Šu'ila to Šamaš]. (http://oracc.org/cams/gkab/P338442)",
            issued={"date-parts": [[2009]]},
            author=[{"family": "Cunningham", "given": "Graham"}],
            **{"container-title": "CAMS/GKAB"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"


def test_implicit_series_part_sibling_is_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="Neue babylonische Planeten-Tafeln II",
            issued={"date-parts": [[1891]]},
            DOI="10.1000/shared",
            **{"container-title": "Zeitschrift für Assyriologie", "volume": "6"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="Neue babylonische Planeten-Tafeln",
            issued={"date-parts": [[1891]]},
            DOI="10.1000/shared",
            **{"container-title": "Zeitschrift für Assyriologie", "volume": "6"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert (
        "series_part" in score.conflicting_signals
        or "doi_data_issue" in score.conflicting_signals
    )


def test_complete_incomplete_dates_are_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="book",
            title=(
                "Documents From the Temple Archives of Nippur, "
                "Dated in the Reigns of Cassite Rulers (Incomplete Dates)"
            ),
            issued={"date-parts": [[1906]]},
            publisher="University Museum",
            **{"container-title": "BE", "collection-title": "BE"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="book",
            title=(
                "Documents From the Temple Archives of Nippur, "
                "Dated in the Reigns of Cassite Rulers (Complete Dates)"
            ),
            issued={"date-parts": [[1906]]},
            publisher="University Museum",
            **{"container-title": "BE", "collection-title": "BE"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"


def test_mixed_candidate_group_splits_unrelated_record() -> None:
    normalized_entries = {
        id_: normalize_entry(data)
        for id_, data in {
            "Steinkeller1989Sale": entry(
                "Steinkeller1989Sale",
                type="book",
                title="Sale Documents of the Ur-III-Period",
                author=[{"family": "Steinkeller", "given": "Piotr"}],
                issued={"date-parts": [[1989]]},
                publisher="Franz Steiner",
                **{"collection-title": "FAOS", "collection-number": "17"},
            ),
            "FAOS_17": entry(
                "FAOS_17",
                type="book",
                title="Sale Documents of the Ur-III-Period",
                author=[{"family": "Steinkeller", "given": "Piotr"}],
                issued={"date-parts": [[1989]]},
                publisher="Franz Steiner",
                **{"collection-title": "FAOS"},
            ),
            "NABU1989-21": entry(
                "NABU1989-21",
                type="article-journal",
                title="Piotr Steinkeller",
                author=[{"family": "Steinkeller", "given": "Piotr"}],
                issued={"date-parts": [[1989]]},
                **{"container-title": "NABU", "volume": "1989"},
            ),
        }.items()
    }
    pairs = [
        score_pair(
            normalized_entries["Steinkeller1989Sale"], normalized_entries["FAOS_17"]
        ),
        score_pair(
            normalized_entries["Steinkeller1989Sale"], normalized_entries["NABU1989-21"]
        ),
    ]
    groups = cluster_pairs(pairs, normalized_entries)

    likely_groups = [
        group for group in groups if group.group_decision == "likely_duplicate"
    ]
    assert len(likely_groups) == 1
    assert set(likely_groups[0].member_ids) == {"Steinkeller1989Sale", "FAOS_17"}


def test_reviewed_not_duplicate_pairs(tmp_path) -> None:
    path = tmp_path / "overrides.json"
    path.write_text(
        '{"notDuplicatePairs":[{"leftId":"B","rightId":"A","reason":"Different volume"}]}',
        encoding="utf-8",
    )
    assert reviewed_not_duplicate_pairs(path) == {("A", "B")}
