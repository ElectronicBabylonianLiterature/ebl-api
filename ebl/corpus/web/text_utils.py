from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.text import TextId
from ebl.errors import NotFoundError
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.genre import Genre


def create_text_id(genre: str, category: str, index: str) -> TextId:
    try:
        return TextId(Genre(genre), int(category), int(index))
    except ValueError as error:
        raise NotFoundError(f"Text {genre} {category}.{index} not found.") from error


def create_chapter_id(
    genre: str, category: str, index: str, stage: str, name: str
) -> ChapterId:
    try:
        full_stage = next(s for s in Stage if stage in (s.long_name, s.abbreviation))
        return ChapterId(create_text_id(genre, category, index), full_stage, name)
    except StopIteration as error:
        raise NotFoundError(f"Stage {stage} does not exist") from error
    except (ValueError, NotFoundError) as error:
        raise NotFoundError(
            f"Chapter {genre} {category}.{index} {stage} {name} not found."
        ) from error
