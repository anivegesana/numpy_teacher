import numpy as np

l1 = np.array([i for i in range(8)])
l2 = np.array([i for i in range(8) if i != 2])
ii = range(8)
l3 = np.array([i for i in ii if i != 2 if i != 3 if i != 1 if i != 4])
l4 = np.array([0 for i in range(10)])

l5 = np.array([0] * 10)
l6 = np.array([2 ** 3] * 20)
l7 = np.array([[2 ** 3] * 20])
l8 = np.array([[[2 ** 3]]] * 20)
