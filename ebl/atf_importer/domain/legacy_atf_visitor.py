from typing import Optional, Sequence, Callable
from lark.visitors import Visitor, Tree
from ebl.atf_importer.domain.legacy_atf_transformers import (
    AccentedIndexTransformer,
    HalfBracketsTransformer,
    OraccJoinerTransformer,
    OraccSpecialTransformer,
    UncertainSignTransformer,
)
from ebl.atf_importer.domain.legacy_atf_transformers import LegacyTransformer

# ToDo: Continue from here
# Make sure every transformer is implemented and works properly.
# Implement the rest, so the maximal possible number of transformations
# happens in the main (ebl) atf grammar.
# Write tests for all transformations!
# After this is done, clean up and get rid of preprocessing
# extept for `# note:` perhaps, if really needed.


index_and_accented_transformer = (AccentedIndexTransformer(), "all_children")
uncertain_sign_transformer = (UncertainSignTransformer(), "all_children")
half_brackets_transformer = (HalfBracketsTransformer(), "all_children")
oracc_joiner_transformer = (OraccJoinerTransformer(), "all_children")
oracc_special_transformer = (OraccSpecialTransformer(), "first_child")


class LegacyAtfVisitor(Visitor):
    text_line_prefix = "ebl_atf_text_line"
    nodes_to_visit = {
        # "number": [index_and_accented_transformer],
        "reading": [index_and_accented_transformer],
        "logogram": [
            index_and_accented_transformer,
            oracc_special_transformer,
        ],
        "surrogate": [index_and_accented_transformer],
        "grapheme": [index_and_accented_transformer],
        "word": [
            uncertain_sign_transformer,
            oracc_joiner_transformer,
        ],
        "text": [half_brackets_transformer],
    }

    def __init__(self):
        super().__init__()
        self.legacy_found = False
        for suffix, transformers in self.nodes_to_visit.items():
            self._set_rules(suffix, transformers)
        print("LegacyAtfVisitor initialized")

    def _set_rules(
        self,
        suffix: str,
        transformers: Sequence[LegacyTransformer],
        prefix: Optional[str] = None,
    ) -> None:
        prefix = prefix if prefix else self.text_line_prefix
        setattr(
            self,
            f"{prefix}__{suffix}",
            self._wrap_transformers(transformers),
        )

    def _wrap_transformers(
        self, transformers: Sequence[LegacyTransformer]
    ) -> Callable[[Tree], None]:
        def _method(tree: Tree) -> Tree:
            for transformer_data in transformers:
                self._transform(tree, *transformer_data)
            return tree

        return _method

    def _transform(self, tree: Tree, transformer: LegacyTransformer, replace: str):
        transformer.clear()
        transformer.current_tree = tree
        transformed_tree = transformer.transform(tree)
        if transformer.legacy_found:
            self.legacy_found = True
            if replace == "first_child":
                tree.children[0] = transformed_tree.children[0]
            elif replace == "all_children":
                tree.children = transformed_tree.children
