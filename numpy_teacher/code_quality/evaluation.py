from numpy_teacher.code_quality.score_functions import *

import os


TEST_DIR = "../../google_code_jam/filtered/"

MATH_EXPR = "math.sqrt(5**2 + 6**2 + (4-3)**2)"
DIST_EXPR = "math.dist([5,6,4], [0, 0, 3])"
HYP_EXPR = "math.hypot(5, 6, 4-3)"
TEST_EXPRESSIONS = [MATH_EXPR, DIST_EXPR, HYP_EXPR]


# Compares the edit distance between the two files and their ordering
def main():
    scoring_methods = [length_scorer, uniform_scorer, uniform_leaf_scorer]
    results = pick_top_k(TEST_DIR, scoring_methods)

    # todo: replace true order
    ordered_test_dir = sorted(os.listdir(TEST_DIR))
    distance_results = get_edit_distance(ordered_test_dir, results)

    print(results)


def get_edit_distance(ordered_dir, results):
    for scoring_method, sorted_tests in results.items():
        score_ordered_dir = [filename for filename, _ in sorted_tests]


# TODO: Conceptually sort out score vs. weight ordering
def pick_top_k(test_dir, score_methods, k=None):
    results = {}

    for score_function in score_methods:
        test_scores = []
        for filename in os.listdir(test_dir):
            filepath = os.path.join(test_dir, filename)
            with open(filepath, "r") as file:
                file_str = file.read()
                score = score_function(file_str)

                test_scores.append((filename, score))

        test_scores.sort(key=lambda x: x[1])
        if k:
            test_scores = test_scores[:k]

        results[score_function.__name__] = test_scores

    print(results)
    return results


def evaluate_test_dir(test_dir, scoring_methods):
    expressions = []
    expression_names = []

    for filename in os.listdir(test_dir):
        filepath = os.path.join(test_dir, filename)
        with open(filepath, "r") as file:
            file_str = file.read()

            expressions.append(file_str)
            expression_names.append(filename)

    print(expressions, expression_names)

    print_expression_names(expression_names)
    evaluate_expressions(expressions, scoring_methods)


def print_expression_names(expression_names):
    for i, name in enumerate(expression_names):
        print(f"expression {i}: {name}")
    print()


def evaluate_expressions(expressions, scoring_methods):

    for score_func in scoring_methods:
        row_str = f"{score_func.__name__}:\t\t"
        for expression in expressions:
            row_str += f"{score_func(expression)} "
        print(row_str)


if __name__ == "__main__":
    main()