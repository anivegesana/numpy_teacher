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


def get_expression_weight(expr, weight_dict=DEFAULT_WEIGHTS):
    # Todo: clean up
    try:
        tree = ast.parse(expr)
    except:
        return 0

    visitor = SimpleWeightedListCompVisitor(weight_dict)
    visitor.visit(tree)

    weight = visitor.weight

    return weight


class SimpleWeightedListCompVisitor(ast.NodeVisitor):
    def __init__(self, weight_dict):
        self.weight = 0
        self.weight_dict = weight_dict

    def generic_visit(self, node):
        if self.weight_dict:
            self.weight += self.weight_dict.get(type(node), 0)
        ast.NodeVisitor.generic_visit(self, node)


if __name__ == "__main__":
    weight = get_expression_weight(TEST_CODE, DEFAULT_WEIGHTS)
    print(weight)
