from ast import *
import dataclasses

from ._core import is_pure

from typing import Union

__all__ = ('analyze_list_to_array', 'get_size_of_list_literal')

class Dimension:
    pass

@dataclasses.dataclass
class ExpandDims(Dimension):
    inner: Union[Dimension, AST]
    dim: int
    def to_ast(self, rewriter):
        np = rewriter.aliases.numpy
        if isinstance(self.inner, AST):
            inner_ast = self.inner
        else:
            inner_ast = self.inner.to_ast(rewriter)
        # np.expand_dims(inner, -1)
        return Call(
            func=Attribute(
                value=Name(id=np, ctx=Load()),
                attr='expand_dims',
                ctx=Load()),
            args=[
                inner_ast,
                Constant(value=self.dim)],
            keywords=[])

@dataclasses.dataclass
class Repeat(Dimension):
    inner: Union[Dimension, AST]
    reps: AST
    dim: int
    def to_ast(self, rewriter):
        np = rewriter.aliases.numpy
        if isinstance(self.inner, AST):
            # Probably always unused because it is expected that inner is either
            # another Repeat in the case we see [...] * i * j or ExpandDims in
            # normal usage.
            inner_ast = self.inner # pragma: no cover
        else:
            inner_ast = self.inner.to_ast(rewriter)
        # np.repeat(inner, reps, -1)
        return Call(
            func=Attribute(
                value=Name(id=np, ctx=Load()),
                attr='repeat',
                ctx=Load()),
            args=[
                inner_ast,
                self.reps,
                Constant(value=self.dim)],
            keywords=[])

def collapse_binop(expr, binop):
    if isinstance(expr, BinOp) and isinstance(expr.op, binop):
        return collapse_binop(expr.left, binop) + collapse_binop(expr.right, binop)
    else:
        return [expr]

def analyze_listcomp(listcomp):
    # print(dump(listcomp, indent=4))
    return listcomp, None, True

def analyze_dimension(listcomp):
    dims = []
    while True:
        match listcomp:
            case List(elts=[elt]):
                listcomp = elt
                dims.append((1, ExpandDims, 0))
            case ListComp():
                listcomp, dim, ret = analyze_listcomp(listcomp)
                if ret:
                    break
                dims.append(dim)
            case BinOp(op=Mult()):
                # TODO: Allow nonconstants if pure or matches correct order
                elts = collapse_binop(listcomp, Mult)
                val, val_found = None, False
                reps = 1
                for elt in elts:
                    if isinstance(elt, Constant):
                        reps *= elt.value
                    elif val_found:
                        # Not possible to rewrite lower than this, at least
                        # for now. Variables in construction will have to wait.
                        break
                    else:
                        val, val_found = elt, True
                listcomp = val
                dims.append((1, Repeat, Constant(reps), 0))
            case _:
                # Stop recursing. No further manipulations can be done.
                break

    # Build a tree representation
    stack = [listcomp]
    for dim in reversed(dims):
        num, const, *args = dim
        subtrees = [stack.pop() for _ in range(num)]
        stack.append(const(*subtrees, *args))
    assert len(stack) == 1
    return stack[0]

def analyze_list_to_array(listcomp, rewriter):
    dims_tree = analyze_dimension(listcomp)
    # print(dims_tree)
    if isinstance(dims_tree, AST):
        return None
    return dims_tree.to_ast(rewriter)

def get_size_of_list_literal(list):
    if hasattr(list, '_are_elems_pure'):
        return None
    plain_elements = 0
    stars = []
    for elt in list.elts:
        if isinstance(elt, Starred):
            # sum(1 for _ in elt.value)
            # likely will change into len later
            stars.append(Call(
                func=Name(id='sum', ctx=Load()),
                args=[
                    GeneratorExp(
                        elt=Constant(value=1),
                        generators=[
                            comprehension(
                                target=Name(id='_', ctx=Store()),
                                iter=elt.value,
                                ifs=[],
                                is_async=0)])],
                keywords=[])
            )
        elif is_pure(elt):
            plain_elements += 1
        else:
            list._are_elems_pure = False
            return None

    if plain_elements == 0:
        if len(stars) == 0:
            return Constant(0)
        else:
            out = stars.pop(0)
    else:
        out = Constant(plain_elements)

    for star in stars:
        out = BinOp(
            left=out,
            op=Add(),
            right=star
        )

    return out
