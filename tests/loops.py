import numpy as np

t1 = [1, 2] * 1 + 1 * [1, 2]
t2 = len(range(min(+1 + 2, 15, -30), max(5 - 1 * 5 / 5, 15)))
t3 = [(i, j) for i in iter(range(8)) for j in range(2)]
t4 = sum(1 for i in enumerate([3, 2, 1], 3))
t5 = list(filter(lambda x: x > 5, range(10)))
t6a = [*np.meshgrid(t5)]
t6b = [*np.meshgrid(t5, indexing="ij")]
*t6c, = [3]
t6d = [*[3, 2]] # doesn't change. tests star
t7 = sum(1 for i in filter(lambda x: x > 5, range(10))) # doesn't change. tests non-len classes in core

l1 = ([i for i in iter(range(8))]) # np.array
l2 = np.array([i for i in range(8) if i != 2])
ii = range(8)
l3 = np.array([i for i in ii if i != 2 if i != 3 if i != 1 if i != 4])
l4 = np.array([0 for i in range(10)])

l5 = np.array([0] * 10)
l6 = np.array([2 ** 3] * 20)
l7 = np.array([[2 ** 3] * 20])
l8 = np.array([[[True] * 2]] * 20)
l9 = np.array([[[0j ** 3] * 2] * 3] * 5)

l10 = np.array([[i + j for i in range(4) if i != 4] for j in range(5) if j != 2])

l11 = -1

l12 = np.array([i*2 for i in range(8)])
l13 = np.stack([np.arange(5)], -1)
