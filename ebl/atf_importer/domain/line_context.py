from typing import List, Optional
from dataclasses import dataclass
from ebl.transliteration.domain.text import TextLine


@dataclass
class LineContext:
    last_transliteration: List[str]
    last_transliteration_line: Optional[TextLine]
    last_alter_lem_line_at: List[int]
