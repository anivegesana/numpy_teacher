from numpy_teacher.code_quality.dataset_loader import dataset_loader

import tqdm

import ast
import pickle

from collections import Counter
from typing import List
import os

TEST_CODE =\
"""
list = [1, 2, 3]
k = [x for x in list]
"""

N_FILES = 10000

# Set of nodes we care about counting frequencies for
AST_NODES = {
    ast.Name,
    ast.Call,
    ast.Constant,
    ast.Assign,
    ast.Attribute,
    ast.ListComp,
    ast.BinOp,
    ast.Subscript,
    ast.Tuple,
    ast.Compare,
    ast.Dict,
    ast.List,
    ast.UnaryOp,
    ast.AnnAssign,
    ast.FunctionDef,
    ast.Return,
    ast.IfExp,
    ast.Lambda,
    ast.BoolOp
}


def main(n_files):
    freq_dict = frequency_analysis("py150", split="train", proportion=1, n_files=n_files)

    with open(os.path.join(os.path.dirname(__file__), f"freq_analysis_{n_files}_files.pkl"), "wb") as freq_file:
        pickle.dump(freq_dict, freq_file)

    print(freq_dict)


def frequency_analysis(dataset_mode="amazing_python", split="train", proportion=1.0, n_files=float('inf'), keys=AST_NODES):
    dataset = dataset_loader(dataset_mode, split, proportion, n_files)
    counter = get_dataset_counter(dataset, keys)

    total_counts = sum(counter.values())
    freq_dict = dict.fromkeys(keys, 0)
    for node in counter:
        freq_dict[node] = counter[node] #/ total_counts

    return freq_dict


def get_dataset_counter(python_files: List[List[str]], keys=AST_NODES):
    counter = Counter()
    for python_file in tqdm.tqdm(python_files):
        for row in python_file:
            row_freqs = get_freq_dict(row, keys=keys)
            counter.update(row_freqs)

    return counter


def get_freq_dict(code_string, keys=AST_NODES):
    try:
        tree = ast.parse(code_string)
    except:
        return {}

    visitor = FrequencyCountVisitor(nodes_of_interest=keys, collect_all=True)
    visitor.visit(tree)
    freq_dict = visitor.freq_dict

    return freq_dict


class FrequencyCountVisitor(ast.NodeVisitor):
    def __init__(self, nodes_of_interest=None, collect_all=False):
        self.freq_dict = {}
        if nodes_of_interest:
            self.freq_dict = dict.fromkeys(nodes_of_interest, 0)
        self.collect_all = collect_all

    def generic_visit(self, node):
        node_type = type(node)
        if self.collect_all:
            self.freq_dict[node_type] = self.freq_dict.get(node_type, 0) + 1
        elif self.freq_dict and node_type in self.freq_dict:
            self.freq_dict[node_type] = self.freq_dict[node_type] + 1
        ast.NodeVisitor.generic_visit(self, node)


if __name__ == "__main__":
    main(N_FILES)
