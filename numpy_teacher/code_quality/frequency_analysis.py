from numpy_teacher.code_quality.dataset_loader import dataset_loader

import ast

from collections import Counter
from typing import List

TEST_CODE =\
"""
list = [1, 2, 3]
k = [x for x in list]
"""


# Set of nodes we care about counting frequencies for
AST_NODES = {
    ast.Name,
    ast.Num
}


def frequency_analysis(dataset_mode="amazing_python", split="train", proportion=1.0, keys=AST_NODES):
    dataset = dataset_loader(dataset_mode, split, proportion)
    counter = get_dataset_counter(dataset, keys)

    total_counts = sum(counter.values())
    freq_dict = dict.fromkeys(keys, 0)
    for node in counter:
        freq_dict[node] = counter[node] / total_counts

    return counter


def get_dataset_counter(python_files: List[List[str]], keys=AST_NODES):
    counter = Counter()
    for python_file in python_files:
        for row in python_file:
            row_freqs = get_freq_dict(row, keys=keys)
            counter.update(row_freqs)

    return counter


def get_freq_dict(code_string, keys=AST_NODES):
    try:
        tree = ast.parse(code_string)
    except:
        return {}

    visitor = FrequencyCountVisitor(nodes_of_interest=keys)
    visitor.visit(tree)
    freq_dict = visitor.freq_dict

    return freq_dict


class FrequencyCountVisitor(ast.NodeVisitor):
    def __init__(self, nodes_of_interest=None):
        self.freq_dict = {}
        if nodes_of_interest:
            self.freq_dict = dict.fromkeys(nodes_of_interest, 0)

    def generic_visit(self, node):
        node_type = type(node)
        if self.freq_dict and node_type in self.freq_dict:
            self.freq_dict[node_type] = self.freq_dict[node_type] + 1
        ast.NodeVisitor.generic_visit(self, node)


if __name__ == "__main__":
    counter = frequency_analysis("amazing_python", split="train", proportion=0.05)
    print(counter)
