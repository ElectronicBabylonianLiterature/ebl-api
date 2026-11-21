from typing import Optional, Sequence

from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.translation_line import TranslationLine


def reconstruction_to_atf(
    reconstruction: Sequence[Token],
    note: Optional[NoteLine],
    parallel_lines: Sequence[ParallelLine],
) -> str:
    return "".join(
        [
            convert_to_atf(None, reconstruction),
            f"\n{note.atf}" if note else "",
            *[f"\n{parallel_line.atf}" for parallel_line in parallel_lines],
        ]
    )


def translation_to_atf(translation: Sequence[TranslationLine]) -> str:
    return "\n".join(translation_line.atf for translation_line in translation)
