import roman  # pyre-ignore[21]
from lark.visitors import Transformer, v_args  # pyre-ignore[21]

from ebl.corpus.domain.chapter import Stage
from ebl.corpus.domain.text import TextId
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.atf import Status, Surface
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    CorpusType,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)


class ParallelLineTransformer(Transformer):  # pyre-ignore[11]
    @v_args(inline=True)  # pyre-ignore[56]
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

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__surface_label(self, surface, status) -> SurfaceLabel:
        return SurfaceLabel.from_label(
            Surface.from_label("".join(surface.children)),
            [Status(token) for token in status.children],
        )

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__parallel_text(
        self, _prefix, cf, text_id, chapter, line_number
    ) -> ParallelText:
        return ParallelText(
            cf is not None, CorpusType.LITERATURE, text_id, chapter, line_number
        )

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__text_id(self, category, number) -> TextId:
        return TextId(roman.fromRoman(category), int(number))

    def ebl_atf_text_line__chapter_name(self, children) -> ChapterName:
        return ChapterName(
            [stage for stage in Stage if stage.abbreviation == children[0]][0],
            "".join(children[1:]),
        )

    def ebl_atf_text_line__parallel_composition(self, children) -> ParallelComposition:
        return ParallelComposition(
            children[1] is not None, "".join(children[2:-1]), children[-1]
        )
