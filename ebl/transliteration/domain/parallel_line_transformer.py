from lark.visitors import v_args
import roman

from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Labels,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)
from ebl.transliteration.domain.common_transformer import CommonTransformer


class ParallelLineTransformer(CommonTransformer):
    def __init__(self):
        super().__init__()

    @v_args(inline=True)
    def ebl_atf_parallel_line__parallel_fragment(
        self,
        _prefix,
        cf,
        museum_number,
        duplicates,
        object_label,
        surface_label,
        column_label,
        line_number,
    ) -> ParallelFragment:
        return ParallelFragment(
            cf is not None,
            museum_number,
            duplicates is not None,
            Labels(object_label, surface_label, column_label),
            line_number,
        )

    def ebl_atf_parallel_line__museum_number(self, children) -> MuseumNumber:
        return MuseumNumber.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_parallel_line__parallel_text(
        self, _prefix, cf, text_id, chapter, line_number
    ) -> ParallelText:
        return ParallelText(cf is not None, text_id, chapter, line_number)

    @v_args(inline=True)
    def ebl_atf_parallel_line__text_id(self, genre, category, number) -> TextId:
        return TextId(
            Genre(genre),
            0 if category == "0" else roman.fromRoman(category),
            int(number),
        )

    @v_args(inline=True)
    def ebl_atf_parallel_line__chapter_name(
        self, stage_abbreviation, version, name
    ) -> ChapterName:
        return self._transform_chapter_name(stage_abbreviation, version, name)

    @v_args(inline=True)
    def chapter_name(self, stage_abbreviation, version, name) -> ChapterName:
        return self._transform_chapter_name(stage_abbreviation, version, name)

    def _transform_chapter_name(self, stage_abbreviation, version, name) -> ChapterName:
        return ChapterName(
            [stage for stage in Stage if stage.abbreviation == stage_abbreviation][0],
            "".join(version.children) if version else "",
            "".join(name.children),
        )

    def ebl_atf_parallel_line__parallel_composition(
        self, children
    ) -> ParallelComposition:
        return ParallelComposition(
            children[1] is not None, "".join(children[2:-1]), children[-1]
        )
