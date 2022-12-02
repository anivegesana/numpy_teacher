from ast import *
import copy
import functools
import os
import types
import warnings

import numpy as np

__all__ = ('Rewriter', 'RestoreReversablesRewriter', 'Warner', 'is_pure', 'is_sized', 'are_all_constants', 'dims_extend', 'dim_repeat')

class Namespace(types.SimpleNamespace):
    def __getattr__(self, attr):
        return None

class Rewriter(NodeTransformer):
    def __init__(self, ctx):
        self.aliases = Namespace()
        self.ctx = ctx
    def visit_Import(self, node):
        for import_alias in node.names:
            if import_alias.name == 'numpy':
                self.aliases.numpy = getattr(import_alias, 'asname', 'numpy')
            if import_alias.name == 'math':
                self.aliases.math = getattr(import_alias, 'asname', 'math')
        return node
    def visit_best(self, *opts):
        quality_score = self.ctx.quality_score
        min_score = float('inf')
        best = None
        for opt in opts:
            # print(unparse(opt), quality_score(opt), min_score)
            if (score := quality_score(opt)) < min_score:
                best = opt
                min_score = score
        return best

class RestoreReversablesRewriter(Rewriter):
    def visit(self, node):
        node = self.generic_visit(node)
        if getattr(node, 'old', None) is not None:
            self.modified = True
            return node.old
        return node

class Warner(NodeVisitor):
    def __init__(self, source, filename='<string>'):
        self.source = source
        self.filename = filename
    def visit(self, node):
        if hasattr(node, 'old'):
            original = get_source_segment(self.source, node)
            new = unparse(node)
            if original:
                if original == new:
                    return self.generic_visit(node)
                msg = original + ' => ' + new
            else:
                msg = new
            warnings.warn_explicit(msg, SyntaxWarning, self.filename, node.lineno)
        else:
            self.generic_visit(node)

# TODO: Work on. Currently unused
class VarRename(NodeTransformer): # pragma: no cover
    def __init__(self, vars, assignments={}):
        self.vars = vars
        self.assignments = assignments

    def visit_Name(self, node):
        if (new_id := self.vars.get(node.id)) is not None:
            node.id = new_id
        if (assign := self.assignments.pop(node.id, None)) is not None:
            return NamedExpr(
                target=node,
                value=assign
            )
        return node

    def visit_FunctionDef(self, node):
        return self.visit_Lambda(node)

    def visit_Lambda(self, node):
        all_args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        argset = {arg.arg for arg in all_args}
        if argset == self.vars.keys():
            return self.generic_visit(node)
        subvars = {k: v for k, v in self.vars.items() if v not in argset}

        # Analyze with different scope
        old_vars = self.vars
        self.vars = subvars
        node = self.generic_visit(node)
        self.vars = old_vars
        return node

    # TODO: handle ast.ClassDef, ast.AsyncFunctionDef, etc.
    # TODO: handle generators and comprehensions

class PurityVisiter(NodeVisitor):
    def __init__(self, name_check=lambda name: False):
        self.name_check = name_check
    @functools.cache
    def visit(self, node):
        f = self.visit
        match node:
            case Constant(value):
                return True
            case Name(id, Load()):
                return self.name_check(id)
            # case Expr(value):
            #     return f(value)
            case NamedExpr(target, value):
                return f(value)
            case UnaryOp(op, operand):
                return f(operand)
            case BinOp(left, op, right):
                return f(left) and f(right)
            case BoolOp(op, values):
                return all(f(v) for v in values)
            case Compare(left, ops, comparators):
                return f(left) and all(f(v) for v in comparators)
            case Tuple(elts, Load()):
                return all(f(v) for v in elts)
            case Slice(lower, upper, step):
                return f(lower) and f(upper) and f(step)
            case Subscript(value, slice, Load()):
                return f(value) and f(slice)
            case _:
                return False

# A convenient shortcut
is_pure = PurityVisiter().visit

def is_sized(classname):
    # TODO: use static analysis to see if a class has a __len__ function available
    # ideally will find out if classname is a subclass of collections.abc.Sized
    if isinstance(classname, Name) and classname.id in ('dict', 'frozenset', 'list', 'range', 'set', 'tuple'):
        return True
    return False

def are_all_constants(l):
    consts = []
    for v in l:
        if not isinstance(v, Constant):
            return None
        consts.append(v.value)
    return consts

def dims_extend(tup, val, dim):
    if isinstance(dim, UnaryOp) and isinstance(dim.op, USub) and isinstance(dim2 := dim.operand, Constant):
        dim = -dim2.value
    elif isinstance(dim, Constant):
        dim = dim.value
    if isinstance(tup, Constant):
        # (tup, val)
        assert dim == 0 or dim == -1
        if dim == 0:
            elts=[val, tup]
        else:
            elts=[tup, val]
        return Tuple(
            elts=elts,
            ctx=Load()
        )
    elif isinstance(tup, Tuple):
        tup = copy.copy(tup)
        if dim == -1:
            tup.elts.append(val)
        elif dim >= 0:
            tup.elts.insert(dim, val)
        else:
            tup.elts.insert(dim+1, val)
        return tup
    raise NotImplementedError # pragma: no cover

def dim_repeat(tup, val, dim):
    if isinstance(dim, UnaryOp) and isinstance(dim.op, USub) and isinstance(dim2 := dim.operand, Constant):
        dim = -dim2.value
    elif isinstance(dim, Constant):
        dim = dim.value
    if isinstance(tup, Constant):
        assert dim == 0 or dim == -1
        if isinstance(val, Constant):
            return Constant(tup.value * val.value)
        else:
            return BinOp(left=tup, op=Mult(), right=val)
    elif isinstance(tup, Tuple):
        tup = copy.copy(tup)
        otup = tup.elts[dim]
        if isinstance(val, Constant):
            tup.elts[dim] = Constant(otup.value * val.value)
        else:
            tup.elts[dim] = BinOp(left=otup, op=Mult(), right=val)
        return tup
    raise NotImplementedError # pragma: no cover
