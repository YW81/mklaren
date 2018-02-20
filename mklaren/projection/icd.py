"""

Incomplete Cholesky Decomposition (CSI) learns low-rank kernel matrix approximation with pivot selection based on lower-bound of the gain of approximation error.

    S. Fine and K. Scheinberg, Efficient SVM Training Using Low-Rank Kernel Representations, J. Mach. Learn. Res., vol. 2, pp. 243-264, 2001.

Given a kernel matrix :math:`\mathbf{K} \in \mathbb{R}^{n\ x\ n}` find a low-rank approximation :math:`\mathbf{G} \in \mathbb{R}^{n\ x\ k}`.


.. math::
    \hat{\mathbf{K}} = \mathbf{G}\mathbf{G}^T

"""

from ..kernel.kinterface import Kinterface
import numpy as np


class ICD:

    """
    :ivar G: (``numpy.ndarray``) Low-rank approximation.
    """

    def __init__(self, rank, eps=1e-10):
        """
        :param rank: (``int``) Maximal decomposition rank.

        :param eps: (``float``)  Tolerance lower bound.
        """
        self.rank = rank
        self.eps = eps
        self.G = None
        self.trained = False
        self.D = None

    def fit(self, K):
        """Learn a low-rank kernel approximation.

        :param K: (``numpy.ndarray``) or of (``Kinterface``). The kernel to be approximated with G.
        """
        n = K.shape[0]
        G = np.zeros((n, self.rank))
        self.D = np.zeros((n, self.rank))
        if isinstance(K, Kinterface):
            D = K.diag().copy()
        else:
            D = np.diag(K).copy()
        J = set(range(n))
        I = list()
        for k in range(self.rank):
            # select pivot d
            self.D[:, k] = D.ravel()
            i = np.argmax(D)
            I.append(i)
            J.remove(i)
            j = list(J)
            G[i, k] = np.sqrt(D[i])
            G[j, k] = 1.0 / G[i, k] * (K[j, i] - G[j, :].dot(G[i, :].T))
            D[j] = D[j] - (G[j, k]**2).ravel()

            # eliminate selected pivot
            D[i] = 0

            # check residual lower bound and maximum rank
            if np.max(D) < self.eps or k + 1 == self.rank:
                break

        self.active_set_ = I
        self.G = G[:, :k+1]
        self.trained = True


    def __call__(self, i, j):
        """
        Access portions of the combined kernel matrix at indices i, j.

        :param i: (``int``) or (``numpy.ndarray``) Index/indices of data points(s).

        :param j: (``int``) or (``numpy.ndarray``) Index/indices of data points(s).

        :return:  (``numpy.ndarray``) Value of the kernel matrix for i, j.
        """
        assert self.trained
        return self.G[i, :].dot(self.G[j, :].T)


    def __getitem__(self, item):
        """
        Access portions of the kernel matrix generated by ``kernel``.

        :param item: (``tuple``) pair of: indices or list of indices or (``numpy.ndarray``) or (``slice``) to address portions of the kernel matrix.

        :return:  (``numpy.ndarray``) Value of the kernel matrix for item.
        """
        assert self.trained
        return self.G[item[0], :].dot(self.G[item[1], :].T)

