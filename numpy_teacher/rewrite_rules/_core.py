from ast import *
import os
import types
import warnings

__all__ = ('Rewriter', 'RestoreReversablesRewriter', 'Warner', 'is_pure', 'is_sized', 'get_shapes_from_list_comprehensions')

class Rewriter(NodeTransformer):
    def __init__(self):
        self.aliases = types.SimpleNamespace()
    def visit_Import(self, node):
        for import_alias in node.names:
            if import_alias.name == 'numpy':
                self.aliases.numpy = getattr(import_alias, 'asname', 'numpy')
        return node

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
            if original:
                msg = original + ' => ' + unparse(node)
            else:
                msg = unparse(node)
            warnings.warn_explicit(msg, SyntaxWarning, self.filename, node.lineno)
        else:
            self.generic_visit(node)

'''
TODO: Work on. Currently unused
class VarRename(NodeTransformer):
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
'''

def is_pure(node):
    # TODO: Add pure functions and constant global variables somehow
    # TODO: Change to PurityVisiter
    match node:
        case Constant(value):
            return True
        case _ if hasattr(node, '_is_pure_cache'):
            return node._is_pure_cache
        case Expr(value):
            node._is_pure_cache = purity = is_pure(value)
            return purity
        case NamedExpr(target, value):
            node._is_pure_cache = purity = is_pure(value)
            return purity
        case UnaryOp(op, operand):
            node._is_pure_cache = purity = is_pure(op)
            return purity
        case BinOp(left, op, right):
            node._is_pure_cache = purity = is_pure(left) and is_pure(right)
            return purity
        case BoolOp(op, values):
            node._is_pure_cache = purity = all(is_pure(v) for v in values)
            return purity
        case Compare(left, ops, comparators):
            node._is_pure_cache = purity = is_pure(left) and all(is_pure(v) for v in comparators)
            return purity
        case Tuple(elts, Load()):
            node._is_pure_cache = purity = all(is_pure(v) for v in elts)
            return purity
        case _:
            return False

def is_sized(classname):
    # TODO: use static analysis to see if a class has a __len__ function available
    if isinstance(classname, Name) and classname.id in ('dict', 'frozenset', 'list', 'range', 'set', 'tuple'):
        return True
    return False

def get_shapes_from_list_comprehensions(lc, num_times, const):
    # TODO: iterate through a series of list comprehensions and find their
    # shapes and return the constant
    return const, None #Tuple(elts=[])
