def _lemma_filter(lemma: str) -> dict:
    return {
        "$filter": {
            "input": "$$variant.manuscripts",
            "as": "manuscript",
            "cond": {
                "$anyElementTrue": [
                    {
                        "$map": {
                            "input": "$$manuscript.line.content.uniqueLemma",
                            "as": "lemmas",
                            "in": {
                                "$in": [
                                    lemma,
                                    "$$lemmas",
                                ]
                            },
                        }
                    }
                ]
            },
        }
    }


def filter_manuscripts_by_lemma(lemma: str) -> dict:
    return {
        "$addFields": {
            "lines.variants": {
                "$map": {
                    "input": "$lines.variants",
                    "as": "variant",
                    "in": {
                        "reconstruction": "$$variant.reconstruction",
                        "intertext": "$$variant.intertext",
                        "parallelLines": "$$variant.parallelLines",
                        "note": "$$variant.note",
                        "manuscripts": _lemma_filter(lemma),
                    },
                }
            }
        }
    }
