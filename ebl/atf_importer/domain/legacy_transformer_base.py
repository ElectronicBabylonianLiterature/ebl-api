from abc import abstractmethod
from typing import (
    Callable,
    Iterator,
    List,
    Optional,
    Protocol,
    Sequence,
    Union,
    cast,
)

from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Discard, Transformer

Branch = Union[str, Tree]
TreeChild = Optional[Union[Tree, Token]]

CreateToken = Callable[[str, Optional[str]], Token]
CreateTree = Callable[[str, Sequence[TreeChild]], Tree]

create_token: CreateToken = cast(CreateToken, Token)
create_tree: CreateTree = cast(CreateTree, Tree)


class TokenAttributes(Protocol):
    type: str
    value: str


def token_type(token: Token) -> str:
    return cast(TokenAttributes, token).type


class TransformerInternals(Protocol):
    __visit_tokens__: bool

    @abstractmethod
    def _transform_tree(self, tree: Tree) -> Branch:
        raise NotImplementedError

    @abstractmethod
    def _call_userfunc_token(self, token: Token) -> Branch:
        raise NotImplementedError


class LegacyTransformer(Transformer):
    prefix = "ebl_atf_text_line"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.legacy_found = False
        self.current_path: List[int] = []
        self.current_tree: Optional[Tree] = None
        self.break_at: Sequence[str] = []

    def clear(self) -> None:
        self.legacy_found = False
        self.current_path = []
        self.current_tree = None

    def transform(self, tree: Tree) -> Tree:
        result = self._remove_discard_nodes(cast(Tree, super().transform(tree)))
        return cast(Tree, result) if result else tree

    def _transform_children(self, children: Sequence[Branch]) -> Iterator[Branch]:
        index_correction = 0
        for index, child in enumerate(children):
            self._enter_node(index - index_correction)
            result = self._get_child_result(child)
            self._exit_node()
            if result is not Discard:
                yield result

    def _get_child_result(self, child: Branch) -> Branch:
        internals = cast(TransformerInternals, self)
        if self.is_classes_break_at(self.get_ancestors()):
            return child
        elif isinstance(child, Tree):
            return internals._transform_tree(child)
        elif internals.__visit_tokens__ and isinstance(child, Token):
            return internals._call_userfunc_token(child)
        else:
            return child

    def _enter_node(self, index: int = 0) -> None:
        self.current_path.append(index)

    def _exit_node(self) -> None:
        if self.current_path:
            self.current_path.pop()

    def get_ancestors(self) -> Sequence[str]:
        if not self.current_tree:
            return []
        tree = self.current_tree
        ancestors = [tree.data]
        for parent_index in self.current_path[:-1]:
            ancestor = cast(Tree, tree.children[parent_index])
            ancestors.append(ancestor.data)
            tree = ancestor
        return ancestors

    def is_classes_break_at(self, node_classes: Sequence[str]) -> bool:
        return not set(node_classes).isdisjoint(self.break_at)

    def _remove_discard_nodes(self, node: Branch) -> Branch:
        if isinstance(node, Tree):
            node.children = [
                self._remove_discard_nodes(child)
                for child in node.children
                if child is not Discard
            ]
        return node

    def _prefixed(self, name: str) -> str:
        return f"{self.prefix}__{name}" if self.prefix else name

    def to_token(self, name: str, string: Optional[str]) -> Token:
        return create_token(self._prefixed(name), string)

    def to_tree(self, name: str, children: Sequence[TreeChild]) -> Tree:
        return create_tree(self._prefixed(name), children)
