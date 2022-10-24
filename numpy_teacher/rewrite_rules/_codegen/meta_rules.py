from ast import *
from .meta_nodes import *

import ast
import collections
import copy
import functools
import itertools
import textwrap
import os
import re

__all__ = ('forall', 'rewriter', 'generate_rewrite_rules', 'UPDATE_VISITOR_POST', 'DEFAULT_POST', 'REVERSIBLE_POST')

class DummyCounter(collections.Counter):
    def __contains__(self, key):
        return False
    def __getitem__(self, key):
        raise KeyError(key)
    def __setitem__(self, key, value):
        return

class ReferenceResolver(NodeTransformer):
    def __init__(self, vars, dummy=False):
        self.vars = vars
        self.counts = DummyCounter() if dummy else collections.Counter()

    def visit_Name(self, node):
        name = node.id

        if name in self.vars:
            var = self.vars[name]

            return var.resolve(node, self.counts)

        if name in globconst.GLOBALS:
            return copy.copy(globconst.GLOBALS[name])

        return node

    def visit_arg(self, node):
        name = node.arg

        if name in self.vars and isinstance(a_var := self.vars[name], var):
            node.arg = escaped(name)

        return node

    def get_reference_identicality_constraint(self):
        if all(cnt == 0 for cnt in self.counts.values()):
            return None
        return ' and '.join(
            ' == '.join([f'{name}', *[
                f'_{name}_{i}'
                for i in range(cnt)
            ]])
            for name, cnt in self.counts.items() if cnt != 0
        )

def _getattr(obj, attr):
    if isinstance(attr, str):
        return getattr(obj, attr)
    else:
        return obj[attr]

UPDATE_VISITOR_POST = 'self.modified = True\ncopy_location(nnode, node)\n'
DEFAULT_POST = UPDATE_VISITOR_POST + 'nnode.old = None'
REVERSIBLE_POST = UPDATE_VISITOR_POST + 'nnode.old = node'

class forall:
    def __init__(self, quantifiers, orig, fin, mode='eval', attr=None, cond=None, post=DEFAULT_POST):
        self.quantifiers = quantifiers
        self.orig = orig
        self.fin = fin
        self.cond = cond
        self.mode = mode

        if attr is None:
            if mode == 'eval':
                attr = ('body', -1, 'value',)
            else:
                attr = ('body',)
            self._attr_default = True
        else:
            self._attr_default = False

        self.attr = attr

        self.post = post

    def get_rules(self, rewriter):
        orig_ast = functools.reduce(_getattr, [parse(self.orig, self.mode), *self.attr])
        fin_ast = functools.reduce(_getattr, [parse(self.fin, self.mode), *self.attr])

        vartypes = {
            var if (tvar := type(var)) is str else var.name: expr(var) if tvar is str else var
            for var in self.quantifiers
        }

        orig_rewrite = ReferenceResolver(vartypes)
        orig_ast = orig_rewrite.visit(orig_ast)
        fin_ast = ReferenceResolver(vartypes, dummy=True).visit(fin_ast)

        match orig_rewrite.get_reference_identicality_constraint(), self.cond:
            case None, None:
                cond = ''
            case cond1, None:
                cond = ' if ' + cond1
            case None, cond2:
                cond = ' if ' + cond2
            case cond1, cond2:
                cond = ' if ' + cond1 + ' and ' + cond2

        return orig_ast, cond, fin_ast

    def __repr__(self):
        arglist = [self.quantifiers, self.orig, self.fin]

        match self.mode, self._attr_default, self.cond:
            case 'eval', True, None:
                pass
            case _, True, None:
                arglist.append(self.mode)
            case _, _, None:
                arglist.extend([self.mode, self.attr])
            case _, _, _:
                arglist.extend([self.mode, self.attr, self.cond])

        return f'{type(self).__name__}({", ".join(map(repr, arglist))})'

_CASE_FINDER = re.compile('case (.*)\(')

def _dump(node, annotate_fields=True, include_attributes=False, *, indent=None):
    if isinstance(node, expr):
        return repr(node)
    return dump(node, annotate_fields, include_attributes, indent=indent)

class rewriter:
    def __init__(self, name, *rules):
        self.name = name
        self.rules = rules

    def dump_code(self, indent_level=4):
        visitors = collections.defaultdict(list[str])

        indent = ' '*indent_level
        for rule in self.rules:
            if isinstance(rule, escaped):
                rule = rule.name
                ast_root = next(line for line in map(str.strip, rule.split('\n')) if line != '' and not line.startswith('#'))
                orig_ast_type = getattr(ast, re.match(_CASE_FINDER, ast_root).group(1))
                visitors[orig_ast_type].append(rule)
                continue
            orig_ast, cond, fin_ast = rule.get_rules(self)
            visitors[type(orig_ast)].append(f"""
# {rule!r}
case {_dump(orig_ast, indent=indent_level)}{cond}:
{indent}nnode = {textwrap.indent(_dump(fin_ast, indent=indent_level), indent)[indent_level:]}"""+
('\n' + textwrap.indent(rule.post, indent) if rule.post else '') + f"""
{indent}return nnode
"""
            )

        for cls in visitors:
            assert issubclass(cls, AST)

        indent2 = ' '*indent_level*2
        indent3 = ' '*indent_level*3
        indent4 = ' '*indent_level*4
        rewritter_code = f'class {self.name}(Rewriter):\n' + '\n'.join([
            f"{indent}def visit_{cls.__name__}(self, node):\n{indent2}match node:" +
            ''.join([textwrap.indent(case, indent3) for case in visitor_cases])
            for cls, visitor_cases in visitors.items()
        ]) + f"\n{indent3}case _:\n{indent4}return self.generic_visit(node)\n"
        # TODO: move node = self.generic_visit(node) to top of function?
        return rewritter_code

    def __repr__(self):
        return f'{type(self).__name__}({self.name!r}, {", ".join(map(repr, self.rules))})'

def generate_rewrite_rules(*rewriters):
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), '_generated.py'), 'w') as f:
        print("""# This file has been generated by a machine. Do NOT modify it directly.
# To modify, go to the "numpy_teacher/rewrite_rules/_codegen/__main__.py" file and
# modify the code that generated this code.

from ast import *
from ._core import *

""", file=f)
        order = []
        for a_rewriter in rewriters:
            match a_rewriter:
                case rewriter():
                    print(a_rewriter.dump_code(), file=f)
                    order.append(a_rewriter.name)
                case escaped():
                    print(a_rewriter.name, file=f)
                case str():
                    order.append(a_rewriter)
        print(f"ORDER = [{', '.join(order)}]\n__all__ = ('ORDER',)\n__all__ += tuple([cls.__name__ for cls in ORDER])", file=f)
