from meta_nodes import *
from meta_rules import *

import textwrap

generate_rewrite_rules(

    rewriter('NumpyRewriter',
        # List comprehensions
        forall([var('v0'), 'in0'], '[v0 for v0 in in0]', 'list(in0)'),
        forall([var('v0'), 'in0', 'in1'], '[v0 for v0 in in0 if in1]', 'list(filter(lambda v0: in1, in0))'), # post=REVERSIBLE_POST

        # Array building
        # TODO: Make these faster by using multilevel matching
        forall(['in0'], 'np.array(range(in0))', 'np.arange(in0)'),
        forall(['in0'], 'np.array(list(in0))', 'np.array(in0)'), # TODO: Check

        forall(['in0', 'in1'], 'np.array(filter(in0, in1))', 'np.extract(in0, np.array(in1))'),

        forall(['in0', 'in1'], 'np.array(in0 * [in1])', 'np.full(in0, in1)'), # TODO: won't work if in1 is a list
        forall(['in0', 'in1'], 'np.array([in1] * in0)', 'np.full(in0, in1)', cond='is_pure(in1) or is_pure(in0)'),
        # TODO: handle constant list comprehensions correctly instead of just this rule
        forall([var('v0'), 'in0', 'in1'], 'np.array([in1 for v0 in in0])', 'np.full(sum(1 for _ in in0), in1)', cond='is_pure(in1)'), # i.e. in1 doesn't have v0 in it. Formalize this in is_pure with bound variables.

        forall(['in0', escaped('Constant(float(0.))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0)'),
        forall(['in0', escaped('Constant(float(1.))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0)'),
        forall(['in0', escaped('Constant(int(0))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=int)'),
        forall(['in0', escaped('Constant(int(1))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=int)'),
        forall(['in0', escaped('Constant(bool(False))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=bool)'),
        forall(['in0', escaped('Constant(bool(True))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=bool)'),
        forall(['in0', escaped('Constant(complex(0+0j))', 'c0')], 'np.full(in0, c0)', 'np.zeros(in0, dtype=complex)'),
        forall(['in0', escaped('Constant(complex(1+0j))', 'c0')], 'np.full(in0, c0)', 'np.ones(in0, dtype=complex)'),

        # Create rules for constant evaluation?
        forall([
            'in0', var('v0'),
            escaped("(Call(func=f0)) as in0", 'x0'),
        ], 'sum(1 for v0 in x0)', 'len(in0)', cond="is_sized(f0)"),
        forall(['in0'], 'len(range(in0))', 'max(in0, 0)'),
        forall(['in0', 'in1'], 'len(range(in0, in1))', 'max(-in0 + in1, 0)'),
        forall(['in0', 'in1'], '-in0 + in1', 'in1 - in0', cond='is_pure(in0) or is_pure(in1)'),
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
