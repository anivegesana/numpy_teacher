from meta_nodes import *
from meta_rules import *

import textwrap

generate_rewrite_rules(

    rewriter('NumpyRewriter',
        # List comprehensions
        forall([var('v0'), 'in0'], '[v0 for v0 in in0]', 'list(in0)'),
        forall([var('v0'), 'in0', 'in1'], '[v0 for v0 in in0 if in1]', 'list(filter(lambda v0: in1, in0))'), # post=REVERSIBLE_POST
        escaped(f"""
# This collapses multiple 'if's that follow each other in the same comprehension
# into one 'if' with multiple 'and's
# TODO: Generalize
case ListComp(
    elt=Name(id=v0, ctx=Load()),
    generators=[
        comprehension(
            target=Name(id=_v0_0, ctx=Store()),
            iter=in0,
            ifs=in1,
            is_async=0)]) if v0 == _v0_0 and len(in1) > 0:
    nnode = Call(
        func=Name(id='list', ctx=Load()),
        args=[
            Call(
                func=Name(id='filter', ctx=Load()),
                args=[
                    Lambda(
                        args=arguments(
                            posonlyargs=[],
                            args=[
                                arg(arg=v0)],
                            kwonlyargs=[],
                            kw_defaults=[],
                            defaults=[]),
                        body=BoolOp(
                            op=And(),
                            values=in1
                        )),
                    in0],
                keywords=[])],
        keywords=[])
{textwrap.indent(DEFAULT_POST, ' ' * 4)}
    return nnode
"""),
        forall([escaped('(ListComp() | List() | BinOp(op=Add() | Mult())) as in0', 'in0'), 'out'], 'np.array(in0)', 'out', cond='(out := analyze_list_to_array(in0, self))'),

        # Array building
        # TODO: Make these faster by using multilevel matching
        forall(['*args'], 'np.array(range(*args))', 'np.arange(*args)'),
        forall(['in0'], 'np.array(list(in0))', 'np.array(in0)'), # TODO: Check

        forall(['in0', 'in1'], 'np.array(filter(in0, in1))', 'np.extract(in0, np.array(in1))'),

        # forall(['in0', 'in1'], 'np.array(in0 * [in1])', 'np.full(in0, in1)'), # TODO: won't work if in1 is a list
        # forall(['in0', 'in1'], 'np.array([in1] * in0)', 'np.full(in0, in1)', cond='is_pure(in1) or is_pure(in0)'),
        # TODO: handle constant list comprehensions correctly instead of just this rule
        forall([var('v0'), 'in0', 'in1'], 'np.array([in1 for v0 in in0])', 'np.full(sum(1 for v0 in in0), in1)', cond='is_pure(in1)'), # i.e. in1 doesn't have v0 in it. Formalize this in is_pure with bound variables.

        # Create rules for constant evaluation?
        forall([
            'in0', var('v0'),
            escaped("(Call(func=f0)) as in0", 'x0'),
        ], 'sum(1 for v0 in x0)', 'len(in0)', cond="is_sized(f0)"),
        forall(['in0'], 'len(range(in0))', 'max(in0, 0)'),
        forall(['in0', 'in1'], 'len(range(in0, in1))', 'max(-in0 + in1, 0)'),
        # TODO: strides

        # TODO: create a constant forall constructor for pure functions:
        constforall(['c0'], '+c0'),
        constforall(['c0'], '-c0'),
        constforall(['c0'], 'not c0'),
        constforall(['c0', 'c1'], 'c0 + c1'),
        constforall(['c0', 'c1'], 'c0 - c1'),
        constforall(['c0', 'c1'], 'c0 * c1'),
        constforall(['c0', 'c1'], 'c0 / c1'),
        constforall(['c0', 'c1'], 'c0 ** c1'),
        constforall(['c0', 'c1'], 'c0 or c1'),
        constforall(['c0', 'c1'], 'c0 and c1'),
        constforall(['c0', 'c1'], 'min(c0, c1)'),
        constforall(['c0', 'c1'], 'max(c0, c1)'),

        forall(['in0', 'in1'], '-in0 + in1', 'in1 - in0', cond='is_pure(in0) or is_pure(in1)'),
        forall(['*cargs'], 'min(*cargs)', 'cval', cond='(cval := are_all_constants(cargs))'),
        forall(['*cargs'], 'max(*cargs)', 'cval', cond='(cval := are_all_constants(cargs))'),

        # Fix strange things that might happen inside of _comprehensions.py
        forall([
            escaped('(Constant() as inner)', 'inner_match'),
            escaped('(Constant(0) | Constant(-1))', 'zono'),
            'inner',
        ], 'np.expand_dims(inner_match, zono)', 'np.full(1, inner)'),
        forall([
            'inner',
            'dims',
            'rdim',
            escaped('dims_extend(dims, Constant(1), rdim)', 'new_dims')
        ], 'np.expand_dims(np.full(dims, inner), rdim)', 'np.full(new_dims, inner)'),
        forall([
            'inner',
            'reps',
            'dims',
            'rdim',
            escaped('dim_repeat(dims, reps, rdim)', 'new_dims')
        ], 'np.repeat(np.full(dims, inner), reps, rdim)', 'np.full(new_dims, inner)'),
        forall(['inner', 'dim'], 'np.stack([inner], dim)', 'np.expand_dims(inner, dim)'),
        forall(['inner', 'dim'], 'np.stack(1 * [inner], dim)', 'np.expand_dims(inner, dim)'),
        forall(['inner', 'dim'], 'np.stack([inner] * 1, dim)', 'np.expand_dims(inner, dim)'),
    ),

    rewriter('NumpySpecialize',
        # Specializations of full
        forall(['in0', escaped('Constant(float(0.))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0)'),
        forall(['in0', escaped('Constant(float(1.))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0)'),
        forall(['in0', escaped('Constant(int(0))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=int)'),
        forall(['in0', escaped('Constant(int(1))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=int)'),
        forall(['in0', escaped('Constant(bool(False))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=bool)'),
        forall(['in0', escaped('Constant(bool(True))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=bool)'),
        forall(['in0', escaped('Constant(complex(0+0j))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=complex)'),
        forall(['in0', escaped('Constant(complex(1+0j))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=complex)'),
    ),

    # 'RestoreReversablesRewriter'
    rewriter('NumpyReverser',
        # forall(['in0'], 'more_itertools.ilen(in0)', 'sum(1 for _ in in0)', cond="not hasattr(self.aliases, 'more_itertools')"),

        # forall([var('v0'), 'in0', 'in1'], '[v0 for v0 in in0 if in1]', 'list(filter(lambda v0: in1, in0))'),
        forall([var('v0'), 'in0', 'in1'], 'list(filter(lambda v0: in1, in0))', '[v0 for v0 in in0 if in1]'),
        # forall(['in0', 'in1'], 'np.array(filter(in0, in1))', 'np.extract(in0, np.array(in1))'),
        forall(['in0', 'in1'], 'np.extract(in0, np.array(in1))', 'np.extract(in0, in1)'),
    )

)
