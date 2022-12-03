import ast


TEST_CODE =\
"""
list = [1, 2, 3]
k = [x for x in list]
"""


# Default weights for the cost model. Each node is weighted accordingly
DEFAULT_WEIGHTS = {
    ast.Name: 1
}


def get_expression_weight(expr, weight_dict=DEFAULT_WEIGHTS, default_weight=0):
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
