from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.text import TextId
from ebl.errors import NotFoundError
from ebl.transliteration.domain.stage import Stage
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
        return ChapterId(
            create_text_id(genre, category, index), Stage.from_name(stage), name
        )
    except (ValueError, NotFoundError) as error:
        raise NotFoundError(
            f"Chapter {genre} {category}.{index} {stage} {name} not found."
        ) from error
