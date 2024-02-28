from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.users.domain.user import Guest


ANY_USER = Guest()


def allow_references(chapter, bibliography):
    for manuscript in chapter.manuscripts:
        for reference in manuscript.references:
            bibliography.create(reference.document, ANY_USER)
        for old_siglum in manuscript.old_sigla:
            bibliography.create(old_siglum.reference.document, ANY_USER)


def allow_signs(signs, sign_list):
    for sign in signs:
        sign_list.create(sign)


def create_chapter_dto(chapter: Chapter) -> dict:
    return ApiChapterSchema().dump(chapter)


def create_chapter_url(chapter: Chapter, suffix: str = "") -> str:
    return (
        f"/texts/{chapter.text_id.genre.value}"
        f"/{chapter.text_id.category}/{chapter.text_id.index}"
        f"/chapters/{chapter.stage.long_name}/{chapter.name}{suffix}"
    )
