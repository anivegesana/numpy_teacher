import os
from datasets import load_dataset

from typing import List

AMAZING_PYTHON_PATH = "shibing624/source_code"
PY_150_PATH = "gpt2/datasets/py150/data/"


# Returns a dataset with shape (n_files, n_rows_in_file)
def dataset_loader(mode="amazing_python", split="train", proportion=1.0) -> List[List[str]]:
    if mode == "amazing_python":
        flat_dataset = load_dataset(AMAZING_PYTHON_PATH, "python")[split]["text"]
        final_dataset = split_by_import(flat_dataset)
        upper_bound = int(len(final_dataset) * min(1.0, proportion))
        return final_dataset[:upper_bound]

    elif mode == "py150":
        final_dataset = collect_python_files(PY_150_PATH)
        upper_bound = int(len(final_dataset) * min(1.0, proportion))
        return final_dataset[:upper_bound]

    else:
        raise NotImplementedError(f"mode '{mode}' does not exist")


# Splits files based on the presence of 'import' keyword.
#   More concretely, the 'import' keyword acts as a positive edge
#   signalling the start of a new file. Subsequent imports after
#   this first edge are ignored.

#     todo: determine a better way to deal with file breaks where there is ambiguity. Some datasets
#         do not have enough information about file boundaries, and so these boundaries may need to be
#         inferred (e.g. 'import' token)
def split_by_import(flat_dataset: List[str]) -> List[List[str]]:
    import_seen = False

    dataset = []
    curr_file = []
    for row in flat_dataset:
        if "import" in row:
            if not import_seen:
                dataset.append(curr_file)
                curr_file = []
                import_seen = True
        else:
            if import_seen:
                import_seen = False
        dataset.append(row)

    return dataset


def collect_python_files(python_repositories_dir: str) -> List[List[str]]:
    dataset = []
    for root, dirs, files in os.walk(python_repositories_dir):
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', errors='ignore') as file:
                        lines = file.readlines()
                        dataset.append(lines)
                except FileNotFoundError:
                    pass

    return dataset
