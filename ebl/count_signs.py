from collections import Counter
from ebl.align import collapse_spaces, map_sign, replace_line_breaks
from ebl.app import create_context
from ebl.corpus.domain.chapter import ChapterId


context = create_context()
repository = context.text_repository

signs = []
for text in repository.list():
    for listing in text.chapters:
        chapter = repository.find_chapter(
            ChapterId(text.id, listing.stage, listing.name)
        )
        signs += [
            sign
            for manuscript in chapter.signs
            for sign in collapse_spaces(replace_line_breaks(manuscript)).split(" ")
            if manuscript
        ]

c = Counter(signs)

for sign, count in c.most_common():
    print(str(count).rjust(6), "\t\t", f"{sign} ({map_sign(sign)})")
