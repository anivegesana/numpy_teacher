from .meta_nodes import *
from .meta_rules import *

import textwrap

generate_rewrite_rules(

    rewriter('NumpyRewriter',
        forall(['in0'], 'np.array(range(in0))', 'np.arange(in0)'),
        forall(['in0'], 'np.array(list(in0))', 'np.array(in0)'), # TODO: Check
        forall([var('v0'), 'in0'], 'np.array([v0 for v0 in in0])', 'np.array(in0)'), # TODO: Check

        escaped(f"""
# Rewrite list repetition as arrays
case Call(
    func=Attribute(
        value=Name(id=self.aliases.numpy, ctx=Load()),
        attr='array',
        ctx=Load()
    ),
    args=[
        BinOp(
            left=in0,
            op=Mult(),
            right=List(
                elts=[in1],
                ctx=Load()
            )
        ) | BinOp(
            left=List(
                elts=[in1],
                ctx=Load()
            ),
            op=Mult(),
            right=in0
        ) | ListComp(
            elt=in1,
            generators=[
                comprehension(
                    target=Name(id=_, ctx=Store()),
                    iter=in0,
                    ifs=[],
                    is_async=0
                )
            ]
        ) as lc
    ],
    keywords=[]
) if is_pure(in1):
    if isinstance(lc, ListComp):
        # In the list comprehension case, we have an iterator, not the size
        # itself.
        in0 = Call(func=Name(id='len', ctx=Load()), args=[in0], keywords=[])

    # TODO: Use recursion to handle nested list comprehensions, not this.
    # is_pure(const := (const_shapes := get_shapes_from_list_comprehensions(lc, in0, in1))[0])
    # shapes = const_shapes[1]
    # if shapes is None or len(shapes.elts) == 0:
    #     shapes = in0
    # else:
    #     shapes.elts.insert(0, in0)
    # Options:
    # np.array([[0]*5 for i in range(4)]).shape
    # np.repeat(np.zeros(5)[np.newaxis, ...], 4, 0).shape
    # np.stack([np.zeros(5)] * 4).shape
    shapes = in0
    const = in1

    match const:
        # TODO: Add many more constant type shortcuts, like complex.
        case Constant(value=0.0):
            attr, args, keywords = 'zeros', [shapes], []
        case Constant(value=1.0):
            attr, args, keywords = 'ones', [shapes], []
        case Constant(value=0):
            attr, args, keywords = 'zeros', [shapes], [
                keyword(arg='dtype', value=Name(id='int', ctx=Load()))
            ]
        case Constant(value=1):
            attr, args, keywords = 'ones', [shapes], [
                keyword(arg='dtype', value=Name(id='int', ctx=Load()))
            ]
        case Constant(value=False):
            attr, args, keywords = 'zeros', [shapes], [
                keyword(arg='dtype', value=Name(id='bool', ctx=Load()))
            ]
        case Constant(value=True):
            attr, args, keywords = 'ones', [shapes], [
                keyword(arg='dtype', value=Name(id='bool', ctx=Load()))
            ]
        case _:
            attr, args, keywords = 'full', [shapes, const], []

    nnode = Call(
        func=Attribute(
            value=Name(id=self.aliases.numpy, ctx=Load()),
            attr=attr,
            ctx=Load()
        ),
        args=args,
        keywords=keywords
    )
{textwrap.indent(DEFAULT_POST, ' '*4)}
    return nnode
"""),

        # Create rules for constant evaluation?
        forall(['in0'], 'len(range(in0))', 'max(in0, 0)'),
        forall(['in0', 'in1'], 'len(range(in0, in1))', 'max(in1 - in0, 0)'),
        # TODO: strides

        # TODO: create a constant forall constructor for pure functions:
        # constforall(['c0', 'c1'], 'max(c0, c1)'),
        escaped(f"""
# Constant evaluation of max
case Call(
    func=Name(id='max', ctx=Load()),
    args=[
        Constant(value=i),
        Constant(value=j)
    ],
    keywords=[]
):
    nnode = Constant(value=max(i, j))
    # TODO: Decide to reverse or not? REVERSIBLE_POST
{textwrap.indent(DEFAULT_POST, ' '*4)}
    return nnode
"""),

    ),

    'RestoreReversablesRewriter'

)
