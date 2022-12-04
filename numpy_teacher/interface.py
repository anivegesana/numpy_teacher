import ast

# import astroid

from numpy_teacher.code_quality import *
from numpy_teacher.context import *
from numpy_teacher.rewrite_rules import *

__all__ = ('rewrite_file',)

def rewrite_file(file, quality_score='uniform_scorer'):
    if isinstance(file, str): # pragma: no cover
        with open(file) as f:
            source = f.read()
        filename = file
    else:
        source = file.read()
        filename = getattr(file, 'name', '<unknown>')
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
