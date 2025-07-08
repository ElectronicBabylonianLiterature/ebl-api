from typing import List
from dataclasses import dataclass


@dataclass
class LineContext:
    last_transliteration: List[str]
    last_transliteration_line: str
    last_alter_lem_line_at: List[int]
