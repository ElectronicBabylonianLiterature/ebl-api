from typing import Sequence, Tuple, Callable
from lark.visitors import Visitor, Tree
from ebl.atf_importer.domain.legacy_atf_transformers import (
    AccentedIndexTransformer,
    HalfBracketsTransformer,
    OraccJoinerTransformer,
    OraccSpecialTransformer,
    UncertainSignTransformer,
    LegacyModifierPrefixTransformer,
    LegacyPrimeTransformer,
    LegacyAlephTransformer,
    LegacyColumnTransformer,
    LegacyTranslationBlockTransformer,
)
from ebl.atf_importer.domain.legacy_atf_transformers import LegacyTransformer

# ToDo: Continue from here
# Make sure every transformer is implemented and works properly.
# Implement the rest, so the maximal possible number of transformations
# happens in the main (ebl) atf grammar.
# Write tests for all transformations!
# After this is done, clean up and get rid of preprocessing
# extept for `# note:` perhaps, if really needed.


index_and_accented_transformer = (AccentedIndexTransformer(), "children")
uncertain_sign_transformer = (UncertainSignTransformer(), "children")
half_brackets_transformer = (HalfBracketsTransformer(), "children")
oracc_joiner_transformer = (OraccJoinerTransformer(), "children")
oracc_special_transformer = (OraccSpecialTransformer(), "children")
oracc_modifier_prefix_transformer = (LegacyModifierPrefixTransformer(), "children")
prime_transformer = (LegacyPrimeTransformer(), "children")
aleph_transformer = (LegacyAlephTransformer(), "children")
column_transformer = (LegacyColumnTransformer(), "tree")
translation_block_transformer = (LegacyTranslationBlockTransformer(), "tree")


class LegacyAtfVisitor(Visitor):
    text_line_prefix = "ebl_atf_text_line"
    at_line_prefix = "ebl_atf_at_line"

    nodes_to_visit = {
        "number": [oracc_modifier_prefix_transformer],
        "reading": [index_and_accented_transformer, oracc_modifier_prefix_transformer],
        "logogram": [
            index_and_accented_transformer,
            oracc_modifier_prefix_transformer,
            oracc_special_transformer,
        ],
        "surrogate": [
            index_and_accented_transformer,
            oracc_modifier_prefix_transformer,
        ],
        "grapheme": [index_and_accented_transformer, oracc_modifier_prefix_transformer],
        "word": [
            uncertain_sign_transformer,
            oracc_joiner_transformer,
        ],
        "text": [half_brackets_transformer],
        "status": [column_transformer],
        "ebl_atf_common__single_line_number": [prime_transformer],
        "value_name_part": [aleph_transformer],
        "at_line_value": [column_transformer],
        "legacy_column": [column_transformer],
        "legacy_translation_line": [translation_block_transformer],
    }

    def __init__(self):
        super().__init__()
        self.legacy_found = False
        for suffix, transformers in self.nodes_to_visit.items():
            prefix = self.text_line_prefix
            if suffix in ["legacy_column"]:
                prefix = self.at_line_prefix
            elif "legacy_translation" in suffix:
                prefix = "" #self.translation_line_prefix
            self._set_rules(suffix, transformers, prefix)

    def _set_rules(
        self,
        suffix: str,
        transformers: Sequence[Tuple[LegacyTransformer, str]],
        prefix: str,
    ) -> None:
        method = f"{prefix}__{suffix}" if prefix else suffix
        print(method)
        setattr(
            self,
            method,
            self._wrap_transformers(transformers),
        )

    def _wrap_transformers(
        self, transformers: Sequence[Tuple[LegacyTransformer, str]]
    ) -> Callable:
        def _method(tree: Tree) -> Tree:
            for transformer_data in transformers:
                self._transform(tree, *transformer_data)
            return tree

        return _method

    def _transform(
        self, tree: Tree, transformer: LegacyTransformer, replace: str
    ) -> None:
        transformer.clear()
        transformer.current_tree = tree
        transformed_tree = transformer.transform(tree)
        if transformer.legacy_found:
            self.legacy_found = True
            if replace == "tree":
                tree.data = transformed_tree.data
                tree.children = transformed_tree.children
            elif replace == "children":
                tree.children = transformed_tree.children
