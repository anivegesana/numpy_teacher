from numpy_teacher.code_quality import lc_tree_weights

import ast


def length_scorer(expr: str):
    return len(expr)


def uniform_scorer(expr: str):
    return lc_tree_weights.get_expression_weight(expr, weight_dict=None, default_weight=1)


def uniform_leaf_scorer(expr: str):
    tree = ast.parse(expr)
    visitor = lc_tree_weights.LeafWeightAccumulator(None, default_weight=1)
    visitor.visit(tree)

    weight = visitor.weight

    return weight
