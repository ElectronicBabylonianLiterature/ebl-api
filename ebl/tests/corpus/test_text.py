import pytest

from ebl.corpus.domain.stage import Stage
from ebl.tests.factories.corpus import ChapterListingFactory, TextFactory


@pytest.mark.parametrize(  # pyre-ignore[56]
    "chapters,expected",
    [
        (tuple(), False),
        (ChapterListingFactory.build_batch(2, stage=Stage.NEO_ASSYRIAN), False),
        (
            [
                ChapterListingFactory.build(stage=Stage.NEO_ASSYRIAN),
                ChapterListingFactory.build(stage=Stage.OLD_ASSYRIAN),
            ],
            True,
        ),
    ],
)
def test_has_multiple_stages(chapters, expected) -> None:
    text = TextFactory.build(chapters=chapters)
    assert text.has_multiple_stages == expected
