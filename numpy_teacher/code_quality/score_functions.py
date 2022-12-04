from numpy_teacher.code_quality import lc_tree_weights

import ast


def length_scorer(expr: str):
    if isinstance(expr, ast.AST):
        return len(ast.unparse(expr))
    else:
        return len(expr)


def uniform_scorer(expr: str):
    return lc_tree_weights.get_expression_weight(expr, weight_dict=None, default_weight=1)


def uniform_leaf_scorer(expr: str):
    if isinstance(expr, ast.AST):
        tree = expr
    else:
        tree = ast.parse(expr)
    visitor = lc_tree_weights.LeafWeightAccumulator(None, default_weight=1)
    visitor.visit(tree)

    weight = visitor.weight

    return weight

def freq_scorer(expr: str):
    return lc_tree_weights.get_expression_weight(expr)

METHODS = {
  'length_scorer': length_scorer,
  'uniform_scorer': uniform_scorer,
  'uniform_leaf_scorer': uniform_leaf_scorer,
  'freq_scorer': freq_scorer,
}

__all__ = (*METHODS, 'METHODS')
