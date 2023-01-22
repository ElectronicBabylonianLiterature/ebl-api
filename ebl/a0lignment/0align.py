import re
from collections import Counter, OrderedDict

import numpy as np
import pyalign
from alignment.vocabulary import Vocabulary

from ebl.aalignment.domain.sequence import make_sequence
from ebl.app import create_context
from ebl.corpus.domain.chapter import ChapterId
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)

def align_chapter_manuscripts(chapter):
    vocabulary = Vocabulary()
    if not any(chapter.signs):
        return Counter()
    else:
        print(f"{chapter.id_}   ".ljust(80, "≡"), end="\n\n", flush=True)

    chapters = []
    fragments = []
    alignments = {}
    for counter, manuscript in enumerate(chapter.manuscripts):
        if has_clear_signs(chapter.signs[counter]):
            chapter_seq = vocabulary.encodeSequence(make_sequence(chapter.signs[counter]))
            chapters.append((manuscript, chapter_seq))
            if manuscript.museum_number is not None:
                try:
                    fragment = context.fragment_repository.query_by_museum_number(
                        manuscript.museum_number
                    )
                    if has_clear_signs(fragment.signs):
                        fragment_seq = vocabulary.encodeSequence(make_sequence(fragment.signs))
                        fragments.append((fragment.number, fragment_seq))
                        alignment = pyalign.global_alignment(np.array(fragment_seq.elements, dtype=np.uint32), np.array(chapter_seq.elements, dtype=np.uint32), gap_Cost=0, eq=2, ne=-0.1)
                        alignments[str(manuscript)] = alignment.score
                except Exception:
                    pass

    chapters_score = {}
    for a in chapters:
        results = []
        for b in fragments:
            alignment = pyalign.global_alignment(np.array(a[1].elements, dtype=np.uint32), np.array(b[1].elements, dtype=np.uint32), gap_Cost=0, eq=2, ne=-0.1)
            results.append((b[0], alignment.score))
        chapters_score[str(a[0])] = sorted(results, key=lambda x: x[1], reverse=True)
    alignments = OrderedDict(sorted(alignments.items()))
    chapters_score = OrderedDict(sorted(chapters_score.items()))
    return alignments, chapters_score




if __name__ == "__main__":
    context = create_context()
    repository = context.text_repository
    chapter = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
    chapter = repository.find_chapter_for_alignment(chapter)

    results = align_chapter_manuscripts(chapter)
    print(results)