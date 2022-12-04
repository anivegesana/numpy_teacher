import ast
import pickle
import os


TEST_CODE =\
"""
list = [1, 2, 3]
k = [x for x in list]
"""

FREQ_FILE = os.path.join(os.path.dirname(__file__), f"freq_analysis_10000_files.pkl")

# Default weights for the cost model. Each node is weighted accordingly
DEFAULT_WEIGHTS = {
    ast.Name: 1
}

try:
    class _Unpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module in ('_ast', 'ast'):
                return getattr(ast, name, None)
            return super().find_class(module, name)
    with open(FREQ_FILE, 'rb') as f:
        DEFAULT_WEIGHTS = _Unpickler(f).load()
    _denom = sum(DEFAULT_WEIGHTS.values())
    for k, v in DEFAULT_WEIGHTS.items():
        DEFAULT_WEIGHTS[k] = 1 - (v / _denom)
except:
    print("Could not get the weights")
    raise


def get_expression_weight(expr, weight_dict=DEFAULT_WEIGHTS, default_weight=0):
    if isinstance(expr, ast.AST):
        tree = expr
    else:
        try:
            tree = ast.parse(expr)
        except:
            return -1

    visitor = SimpleWeightAccumulator(weight_dict, default_weight)
    visitor.visit(tree)

    weight = visitor.weight

    return weight


class SimpleWeightAccumulator(ast.NodeVisitor):
    def __init__(self, weight_dict, default_weight=0):
        self.weight = 0
        self.weight_dict = weight_dict
        self.default_weight = default_weight

    def generic_visit(self, node):
        if self.weight_dict:
            self.weight += self.weight_dict.get(type(node), self.default_weight)
        else:
            self.weight += self.default_weight
        ast.NodeVisitor.generic_visit(self, node)


class LeafWeightAccumulator(ast.NodeVisitor):
    def __init__(self, weight_dict, default_weight=0):
        self.weight = 0
        self.weight_dict = weight_dict
        self.default_weight = default_weight

    def generic_visit(self, node):
        child_nodes = ast.iter_child_nodes(node)

        if len(list(child_nodes)) == 0:
            if self.weight_dict:
                self.weight += self.weight_dict.get(type(node), self.default_weight)
            else:
                self.weight += self.default_weight

        ast.NodeVisitor.generic_visit(self, node)


if __name__ == "__main__":
    weight = get_expression_weight(TEST_CODE, DEFAULT_WEIGHTS)
    print(weight)
