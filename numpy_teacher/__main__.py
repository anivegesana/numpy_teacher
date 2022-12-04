import argparse
import traceback

from numpy_teacher.code_quality import *
from numpy_teacher.interface import rewrite_file

parser = argparse.ArgumentParser(description='A linter that teaches beginners how to use Numpy.')
parser.add_argument('source', type=argparse.FileType('r'), nargs='+',
                    help='file to lint')
parser.add_argument('--quality_score', type=str, choices=METHODS,
                    default=rewrite_file.__defaults__[0],
                    help='code quality metric', required=False)
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
