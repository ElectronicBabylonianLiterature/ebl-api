from typing import Optional, Sequence


def filter_by_script(
    script_period: Optional[str] = None, script_period_modifier: Optional[str] = None
) -> dict:
    parameters = {
        "script.period": script_period,
        "script.periodModifier": script_period_modifier,
    }
    return {path: value for path, value in parameters.items() if value}


def filter_by_genre(genre: Optional[Sequence[str]] = None) -> dict:
    return {"genres.category": {"$all": genre}} if genre else {}
