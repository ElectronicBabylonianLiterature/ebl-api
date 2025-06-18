from lark import Transformer
from copy import deepcopy


def add_namespace(transformer: Transformer, prefix: str):
    base_transformer = deepcopy(transformer)

    for method_name in dir(transformer):
        method = getattr(transformer, method_name)
        if not callable(method):
            continue
        if method_name.startswith("_") or method_name == "transform":
            continue
        prefixed_method = prefix + "__" + method_name

        setattr(base_transformer, prefixed_method, method)

    print(base_transformer)
    print(*dir(base_transformer), sep="\n")
    print()
    return base_transformer
