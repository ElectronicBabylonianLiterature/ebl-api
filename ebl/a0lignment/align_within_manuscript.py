import time
from collections import Counter, OrderedDict

import pyalign

from ebl.a0lignment.utils import has_clear_signs
from ebl.a0lignment.vocabulary import SignsVocabulary
from ebl.app import create_context
from ebl.corpus.domain.chapter import ChapterId
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


def global_align(a, b):
    return pyalign.global_alignment(a.sequence, b.sequence, gap_Cost=0, eq=2, ne=-0.1)


def align_chapter_manuscripts(chapter, vocabulary):
    if not any(chapter.signs):
        return Counter()
    else:
        print(f"{chapter.id_}   ".ljust(80, "≡"), end="\n\n", flush=True)

    # keep score of each manuscript and it's associated fragment
    chapters = []
    fragments = []
    manuscript_associated_scores = {}
    for index, manuscript in enumerate(chapter.manuscripts):
        if has_clear_signs(chapter.signs[index]):
            chapter_seq = vocabulary.encodeToNamedSeq(manuscript.siglum, chapter.signs[index])
            chapters.append(chapter_seq)
            if manuscript.museum_number is not None:
                try:
                    fragment = context.fragment_repository.query_by_museum_number_alignment(
                        manuscript.museum_number
                    )
                    signs = fragment["signs"]
                    if has_clear_signs(signs):
                        fragment_seq = vocabulary.encodeToNamedSeq(fragment["_id"], signs)
                        fragments.append(fragment_seq)
                        alignment = global_align(chapter_seq, fragment_seq)
                        manuscript_associated_scores[chapter_seq.name] = {fragment_seq.name: round(alignment.score, 2)}
                except Exception:
                    pass

    # keep score of every combination of manuscripts and fragments within a chapter
    all_scores = {}
    for a in chapters:
        results = []
        for b in fragments:
            alignment = global_align(a, b)
            results.append((b.name, round(alignment.score, 2)))
        all_scores[a.name] = sorted(results, key=lambda x: x[1], reverse=True)

    manuscript_associated_scores = OrderedDict(sorted(manuscript_associated_scores.items()))
    all_scores = OrderedDict(sorted(all_scores.items()))
    return manuscript_associated_scores, all_scores



if __name__ == "__main__":
    t0 = time.time()
    context = create_context()
    repository = context.text_repository
    fragments = context.fragment_repository

    chapter = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
    chapter = repository.find_chapter_for_alignment(chapter)
    signs = context.sign_repository.find_many({})
    vocabulary = SignsVocabulary(signs)

    results = align_chapter_manuscripts(chapter, vocabulary)
    print("Done")