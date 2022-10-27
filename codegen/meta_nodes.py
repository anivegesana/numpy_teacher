from ast import *
import collections
import copy

from typing import ClassVar

__all__ = ('expr', 'escaped', 'var', 'globconst')

# Nodes for a higher level domain specific language for specifying AST patterns

class expr:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f'{type(self).__name__}({self.name!r})'
    def resolve(self, node: Name, counts: collections.Counter) -> 'escaped':
        name = self.name

        if name not in counts:
            counts[name] = 0
            return escaped(name)
        else:
            raise ValueError(f'Duplicate name for variable {self.name}.')

        return node

class escaped(expr):
    def __init__(self, code, name=None):
        self.name = name
        self.code = code
    def __repr__(self):
        return self.code
    def __iter__(self):
        yield self
    def resolve(self, node, counts):
        return self

class var(expr):
    def resolve(self, node, counts):
        name = self.name

        if name not in counts:
            node.id = escaped(name)
            counts[name] = 0
        else:
            node.id = escaped(f'_{name}_{counts[name]}')
            counts[name] += 1

        return node

class globconst(expr):
    GLOBALS: ClassVar[dict[str, AST]] = {
        'np': Name(id=escaped('self.aliases.numpy'), ctx=Load())
    }
    def __init__(self, name, node=None):
        self.name = name
        if node is None:
            self.node = self.GLOBALS[name]
        else:
            self.node = node
    def resolve(self, node, counts):
        return copy.copy(self.node)
