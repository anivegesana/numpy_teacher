import numpy as np

i = 4

zf = np.array([[[0.0 ** 3] * 2] * 3] * 5)
of = np.array([[[1.0 ** 3] * 2] * 3] * 5)
zb = np.array([[[True and not True] * 2] * 3] * 5)
ob = np.array([[[True or not True] * 2] * 3] * 5)
zi = np.array([[[0 ** 3] * 2] * 3] * 5)
oi = np.array([[[1 ** 3] * 2] * 3] * 5)
zc = np.array([[[0j ** 3] * 2] * 3] * 5)
oc = np.array([[[(-1j) ** 4] * 2] * 3] * 5)
noc = np.array([[[1j ** 3] * 2] * 3] * 5)

x1 = np.expand_dims(np.full((2, 3, 4), 8), -1)
x2 = np.expand_dims(np.full((2, 3, 4), 8), -2)
x3 = np.expand_dims(np.full(2, 8), -1)

r1 = np.repeat(np.full((2, 3, 4), 8), 3, -1)
r2 = np.repeat(np.full((2, 3, 4), 8), i, -1)
r3 = np.repeat(np.full(3, 8), i, -1)
r4 = np.array([1j ** 3] * 2 * i * 5) # irreducible for now

pure_test = np.array([(a := (2, -3)[1:][0] > 3) or True for i in range(50)])

ll1 = len([])
ll2 = len([object()])
ll3 = len([1, 3, *(4, 3, 3)])
ll4 = len([*(4, 3, 3), *[3, 2, 1]])
