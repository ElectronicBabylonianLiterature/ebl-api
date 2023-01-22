import re

def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)
