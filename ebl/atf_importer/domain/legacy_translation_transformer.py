import re
from typing import Optional, List, Sequence, Union, cast
from lark.visitors import Tree, Token, v_args
from ebl.transliteration.domain.common_transformer import CommonTransformer
from ebl.atf_importer.domain.legacy_atf_transformers import LegacyTransformer


class LegacyTranslationBlockTransformer(LegacyTransformer):
    prefix = ""
    _markup_pattern = re.compile(r"@\?(.*?)\?@|@([^\s@][^\s]*)")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.reset()

    def reset(self) -> None:
        self.language: Optional[Token] = None
        self.start: Optional[str] = None
        self.extent: List[Tree] = []
        self.translation: List[str] = []

    @property
    def translation_c_line(self) -> Tree:
        return self.to_tree(
            "!translation_line",
            [
                self.language,
                self._translation_extent,
            ]
            + list(cast(List[Union[None, Token, Tree]], self._translation_parts)),
        )

    @v_args(inline=True)
    def ebl_atf_translation_line__legacy_translation_block_at_line(
        self, language: Optional[Token]
    ) -> None:
        self.reset()
        self.legacy_found = True
        self.language = language
        return

    @v_args(inline=True)
    def ebl_atf_translation_line__labels_start(self, labels: Tree) -> None:
        self.reset()
        self.legacy_found = True
        self.start = self._labels_to_string(labels)
        return

    @v_args(inline=True)
    def ebl_atf_translation_line__labels_extent(self, labels: Tree) -> None:
        self.legacy_found = True
        self.extent = labels.children
        return

    @v_args(inline=True)
    def ebl_atf_translation_line__legacy_translation_block_line(
        self, text: Tree
    ) -> Tree:
        self.legacy_found = True
        self.translation.append("".join([str(child) for child in text.children]))
        return self.translation_c_line

    def ebl_atf_translation_line__legacy_translation_block_label_text_line(
        self, line: Sequence[Tree]
    ) -> Tree:
        return line[1]

    def _labels_to_string(self, labels: Tree) -> str:
        labels, line_number = CommonTransformer().transform(labels).children
        return (
            " ".join(label.to_value() for label in labels)
            + " "
            + str(line_number.number)
        )

    @property
    def _translation_extent(self) -> Optional[Tree]:
        return (
            self.to_tree(
                "ebl_atf_translation_line__translation_extent",
                cast(List[Union[None, Token, Tree]], self.extent),
            )
            if self.extent
            else None
        )

    @property
    def _translation_parts(self) -> List[Tree]:
        raw_text = " ".join(self.translation).replace(r"/[\s]+/", " ")
        text_with_literals = self._convert_literal_quotes(raw_text)
        segments = self._split_markup_segments(text_with_literals)
        return [self._build_tree_segment(text, type) for text, type in segments]

    def _convert_literal_quotes(self, text: str) -> str:
        return re.sub(r'@"(.*?)"@', r"“\1”", text)

    def _build_tree_segment(self, text: str, type: str) -> Tree:
        token = self.to_token("__ANON_26", text)
        note_text = self.to_tree(
            "ebl_atf_translation_line__ebl_atf_note_line__note_text", [token]
        )
        rule = (
            "ebl_atf_translation_line__ebl_atf_note_line__emphasis_part"
            if type == "emphasis"
            else "ebl_atf_translation_line__ebl_atf_note_line__string_part"
        )
        return self.to_tree(rule, [note_text])

    def _split_markup_segments(self, text: str) -> List[tuple[str, str]]:
        segments = []
        last_index = 0
        for match in self._markup_pattern.finditer(text):
            start, end = match.span()
            if start > last_index:
                segments.append((text[last_index:start], "string"))
            matched_text = match.group(1) or match.group(2)
            segments.append((matched_text, "emphasis"))
            last_index = end
        if last_index < len(text):
            segments.append((text[last_index:], "string"))
        return segments
