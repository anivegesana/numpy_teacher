import argparse
import ast
import traceback

# import astroid

from numpy_teacher.code_quality import *
from numpy_teacher.context import *
from numpy_teacher.rewrite_rules import *

def rewrite_file(file, quality_score):
    if not hasattr(file, 'name'): # pragma: no cover
        with open(file) as f:
            source = f.read()
        filename = file
    else:
        source = file.read()
        filename = file.name
    ast_ = ast.parse(source, filename)

    ctx = Context()
    ctx.filename = filename
    ctx.quality_score = METHODS[quality_score]

    std_rewrites = [
        cls(ctx)
        for cls in ORDER
    ]

    rewrites = std_rewrites

    for rewrite in rewrites:
        for i in range(100):
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
parser.add_argument('source', type=argparse.FileType('r'), nargs='+',
                    help='file to lint')
parser.add_argument('--quality_score', type=str, choices=METHODS,
                    default='lc_tree_weights', help='code quality metric',
                    required=False)
args = parser.parse_args()

for source in args.source:
    if len(args.source) != 1:
        print()
        print(source.name)
        print("=====")
    try:
        print(rewrite_file(source, args.quality_score))
    except:
        traceback.print_exc()

# std_rewrites = [
#     LoopToArrayRewriter(),
#     PyBuiltinToNumpyFuncRewriter(),
# ]


# def apply_rewrites(rewrites: list[Rewriter], ast_: AST):
#     for rewrite in rewrites:
#         ast_ = ast_.visit(rewrite)
#     return ast_
