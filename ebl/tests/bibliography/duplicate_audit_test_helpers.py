from ebl.bibliography.application.duplicate_audit import normalize_entry, score_pair


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


def score_entries(
    left_overrides, right_overrides, *, previously_reviewed_not_duplicate: bool = False
):
    return score_pair(
        normalize_entry(entry("A", **left_overrides)),
        normalize_entry(entry("B", **right_overrides)),
        previously_reviewed_not_duplicate=previously_reviewed_not_duplicate,
    )


def score_entries_with_shared_overrides(
    shared_overrides, left_overrides, right_overrides
):
    return score_entries(
        {**shared_overrides, **left_overrides},
        {**shared_overrides, **right_overrides},
    )
