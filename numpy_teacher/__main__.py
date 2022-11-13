import argparse
import ast

from numpy_teacher.rewrite_rules import *

def rewrite_file(file):
    std_rewrites = [
        cls()
        for cls in ORDER
    ]

    rewrites = std_rewrites

    if not hasattr(file, 'name'):
        with open(file) as f:
            source = f.read()
        filename = file
    else:
        source = file.read()
        filename = file.name
    ast_ = ast.parse(source, filename)

    for rewrite in rewrites:
        for i in range(55):
            rewrite.modified = False
            ast_ = rewrite.visit(ast_)
            # print(ast.unparse(ast_))
            # print(f'{rewrite} -====-')
            if not rewrite.modified:
                break

    ast.fix_missing_locations(ast_)
    Warner(source, filename).visit(ast_)
    return ast.unparse(ast_)


parser = argparse.ArgumentParser(description='A linter that teaches beginners how to use Numpy.')
parser.add_argument('source', type=argparse.FileType('r'),
                    help='file to lint')
args = parser.parse_args()

print(rewrite_file(args.source))

# std_rewrites = [
#     LoopToArrayRewriter(),
#     PyBuiltinToNumpyFuncRewriter(),
# ]


# def apply_rewrites(rewrites: list[Rewriter], ast_: AST):
#     for rewrite in rewrites:
#         ast_ = ast_.visit(rewrite)
#     return ast_
