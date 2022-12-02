from meta_nodes import *
from meta_rules import *

import textwrap

generate_rewrite_rules(

    rewriter('PythagoreanRewriter',
        # A fork in the road, a rule that requires a choice
        forall([
            'in0',
            'opts',
            escaped('opts[0]', 'opt0'),
            escaped('opts[1]', 'opt1'),
            escaped('*opts[2]', 'opt2'),
        ], 'math.sqrt(in0)', choices(
            'math.dist(opt0, opt1)',
            'math.hypot(opt2)'
        ), cond='opts := resolve_pythagorean(in0)'),
    ),

    rewriter('ComprehensionRewriter',
        escaped(f"""
# This collapses multiple 'if's that follow each other in the same comprehension
# into one 'if' with multiple 'and's
case comprehension(
        target=target,
        iter=in0,
        ifs=in1,
        is_async=is_async) if len(in1) > 1:
    nnode = comprehension(
        target=target,
        iter=in0,
        ifs=[BoolOp(
            op=And(),
            values=in1
        )],
        is_async=is_async)
    nnode.lineno = target.lineno
{textwrap.indent(DEFAULT_POST, ' ' * 4)}
    return nnode
# Remove unnecesary iter
case comprehension(
        target=target,
        iter=Call(
            func=Name(id='iter', ctx=Load()),
            args=[in0],
            keywords=[]
        ),
        ifs=in1,
        is_async=is_async):
    nnode = comprehension(
        target=target,
        iter=in0,
        ifs=in1,
        is_async=is_async)
    nnode.lineno = target.lineno
{textwrap.indent(DEFAULT_POST, ' ' * 4)}
    return nnode
""")
    ),

    rewriter('NumpyRewriter',
        # List comprehensions
        forall([var('v0'), 'in0'], '[v0 for v0 in in0]', 'list(in0)'),
        forall([var('v0'), 'in0'], '*v0, = in0', 'v0 = list(in0)', mode='exec'),
        forall([var('v0'), 'in0', 'in1'], '[v0 for v0 in in0 if in1]', 'list(filter(lambda v0: in1, in0))'), # post=REVERSIBLE_POST

        # forall(['*args'], '1 * [*args]', '[*args]'),
        forall(['*elts', escaped('List() | ListComp() as val', 'val_match'), 'val'],
                '1 * val_match', 'val'),
        forall(['*elts', escaped('List() | ListComp() as val', 'val_match'), 'val'],
                'val_match * 1', 'val'),
        forall([escaped('(ListComp() | List() | BinOp(op=Add() | Mult())) as in0', 'in0'), 'out'], 'np.array(in0)', 'out', cond='(out := analyze_list_to_array(in0, self))'),

        # Array building
        # TODO: Make these faster by using multilevel matching
        forall(['*args', '^1'], 'np.array(range(*args), ^1)', 'np.arange(*args, ^1)'),
        forall(['in0', '^1'], 'np.array(list(in0), ^1)', 'np.array(in0, ^1)'), # TODO: Check

        forall(['in0', 'in1'], 'np.array(filter(in0, in1))', 'np.extract(in0, np.array(in1))'),

        # TODO: handle constant list comprehensions correctly instead of just this rule
        forall([var('v0'), 'in0', 'in1'], 'np.array([in1 for v0 in in0])', 'np.full(sum(1 for v0 in in0), in1)', cond='is_pure(in1)'), # i.e. in1 doesn't have v0 in it. Formalize this in is_pure with bound variables.

        # Create rules for constant evaluation?
        forall(['v0', 'in0', '^1'], 'sum(1 for v0 in enumerate(in0, ^1))', 'sum(1 for v0 in in0)'),
        forall([
            'in0', var('v0'),
            escaped("(Call(func=f0)) as in0", 'x0'),
        ], 'sum(1 for v0 in x0)', 'len(in0)', cond="is_sized(f0)"),
        forall([
            'in0', var('v0'),
            escaped("List() | ListComp() | Tuple() | Set() | SetComp() | Dict() | DictComp() as in0", 'x0'),
        ], 'sum(1 for v0 in x0)', 'len(in0)'),
        forall(['in0'], 'len(range(in0))', 'max(in0, 0)'),
        forall(['in0', 'in1'], 'len(range(in0, in1))', 'max(-in0 + in1, 0)'),
        forall([
            'in0', 'in1',
            escaped("List(elts=elts0) as in0", 'x0'),
            escaped("List(elts=elts1) as in1", 'x1'),
            escaped("List(elts=elts0+elts1)", 'x2'),
        ], 'x0 + x1', 'x2'),
        forall([
            'in0', 'size',
            escaped("(List() | Tuple()) as in0", 'x0'),
        ], 'len(x0)', 'size', cond='size := get_size_of_list_literal(in0)'),
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
        constforall(['c0'], 'abs(c0)'),
        # constforall(['c0', 'c1'], 'min(c0, c1)'),
        # constforall(['c0', 'c1'], 'max(c0, c1)'),

        forall(['in0', 'in1'], '-in0 + in1', 'in1 - in0', cond='is_pure(in0) or is_pure(in1)'),
        forall(['*cargs', escaped('Constant(min(*cval))', 'cmin')], 'min(*cargs)', 'cmin', cond='(cval := are_all_constants(cargs))'),
        forall(['*cargs', escaped('Constant(max(*cval))', 'cmax')], 'max(*cargs)', 'cmax', cond='(cval := are_all_constants(cargs))'),

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
        forall(['in0'], '*np.meshgrid(in0)', 'in0'),
        forall(['in0'], '*np.meshgrid(in0, indexing="ij")', 'in0'), # TODO: for products, maybe?
        # forall([var('v0'), 'in0', 'in1'], '(lambda v0: in0)(in1)', 'in0', cond='is_pure(in0, pure_filter_accept_once(v0.id))'),
    ),

    rewriter('NumpySpecialize',
        # Specializations of full
        forall(['in0', escaped('Constant((0. as cv0))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0)', cond='isinstance(cv0, float)'),
        forall(['in0', escaped('Constant((1. as cv0))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0)', cond='isinstance(cv0, float)'),
        forall(['in0', escaped('Constant((False as cv0))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=bool)', cond='isinstance(cv0, bool)'),
        forall(['in0', escaped('Constant((True as cv0))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=bool)', cond='isinstance(cv0, bool)'),
        forall(['in0', escaped('Constant((0 as cv0))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=int)', cond='isinstance(cv0, int)'),
        forall(['in0', escaped('Constant((1 as cv0))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=int)', cond='isinstance(cv0, int)'),
        forall(['in0', escaped('Constant((0+0j as cv0))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=complex)', cond='isinstance(cv0, complex)'),
        forall(['in0', escaped('Constant((1+0j as cv0))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=complex)', cond='isinstance(cv0, complex)'),
    ),

    # 'RestoreReversablesRewriter'
    rewriter('NumpyReverser',
        # forall(['in0'], 'more_itertools.ilen(in0)', 'sum(1 for _ in in0)', cond="not hasattr(self.aliases, 'more_itertools')"),

        # forall([var('v0'), 'in0', 'in1'], '[v0 for v0 in in0 if in1]', 'list(filter(lambda v0: in1, in0))'),
        forall([var('v0'), 'in0', 'in1'], 'list(filter(lambda v0: in1, in0))', '[v0 for v0 in in0 if in1]'),
        # forall(['in0', 'in1'], 'np.array(filter(in0, in1))', 'np.extract(in0, np.array(in1))'),
        forall(['in0', 'in1'], 'np.extract(in0, np.array(in1))', 'np.extract(in0, in1)'),
    ),

    "RestoreReversablesRewriter",

)
