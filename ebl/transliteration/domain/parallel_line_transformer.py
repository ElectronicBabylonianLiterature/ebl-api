from lark.visitors import v_args
import roman

from ebl.corpus.domain.chapter import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.labels import LabelTransformer
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Genre,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)


class ParallelLineTransformer(LabelTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__parallel_fragment(
        self, _prefix, cf, museum_number, duplicates, surface_label, line_number
    ) -> ParallelFragment:
        return ParallelFragment(
            cf is not None,
            museum_number,
            duplicates is not None,
            surface_label,
            line_number,
        )

    def ebl_atf_text_line__museum_number(self, children) -> MuseumNumber:
        return MuseumNumber.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__parallel_text(
        self, _prefix, cf, text_id, chapter, line_number
    ) -> ParallelText:
        return ParallelText(
            cf is not None, Genre.LITERATURE, text_id, chapter, line_number
        )

    @v_args(inline=True)
    def ebl_atf_text_line__text_id(self, category, number) -> TextId:
        return TextId(0 if category == "0" else roman.fromRoman(category), int(number))

    @v_args(inline=True)
    def ebl_atf_text_line__chapter_name(
        self, stage_abbreviation, version, name
    ) -> ChapterName:
        return ChapterName(
            [stage for stage in Stage if stage.abbreviation == stage_abbreviation][0],
            "".join(version.children) if version else "",
            "".join(name.children),
        )

    def ebl_atf_text_line__parallel_composition(self, children) -> ParallelComposition:
        return ParallelComposition(
            children[1] is not None, "".join(children[2:-1]), children[-1]
        )
