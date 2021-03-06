import numpy as np
from sklearn.linear_model.ridge import Ridge


class Arima:

    """ Learn an average of rank number of previous points.

        Allow for different modes of planting the inducing points:
            recent: most recent points
            linear: equally-spread points.
            log: logarithmic spread with emphasis on more recent points.

        The burden to input a sensible dataset (enough history to predict all points)
        is placed on the user.
    """

    def __init__(self, rank, **kwargs):
        self.rank = rank
        self.kwargs = kwargs
        self.X = None
        self.y = None
        self.models = dict()

    def fit(self, X, y):
        """
        X are indices from 0 ... n.
        Extrapolation works for points up to n + tau_max.
        """
        assert X.dtype == np.dtype("int")
        rank = self.rank

        # Sort if not sorted
        inxs = np.argsort(X.ravel())
        X = X[inxs]
        y = y[inxs]
        self.X = X
        self.y = y

        # Extract statistics
        n = len(X)
        tau_max = n - 2 * rank

        # Construct design matrix and model for each tau
        for tau in range(1, tau_max + 1):
            M = np.zeros((n - tau - rank, rank))
            Y = np.zeros((n - tau - rank,))
            for i, end in enumerate(range(rank, n - tau)):
                start = end - rank
                M[i] = y[X[start:end]].ravel()
                Y[i] = y[X[end] + tau]
            tau_model = Ridge(**self.kwargs)
            tau_model.fit(M, Y)
            self.models[tau] = tau_model

    def predict(self, X):
        """ Predict values Tau steps in the future. """
        rank = self.rank
        tau_max = max(self.models.keys())
        yp = np.zeros((len(X),))
        for xi, x in enumerate(X):
            tau = np.min(np.absolute(x - self.X))
            if tau == 0:
                # Interpolation
                i = int(np.where(self.X == x)[0])
                if i < rank:
                    yp[xi] = self.y[i]
                else:
                    eff_tau = 1
                    m = self.y[i - rank + 1:i + 1].reshape((1, rank))
                    yp[xi] = self.models[eff_tau].predict(m)
            elif tau > 0:
                # Extrapolation
                m = self.y[-rank:].reshape((1, rank))
                eff_tau = min(tau, tau_max)
                yp[xi] = self.models[eff_tau].predict(m)
            else:
                raise ValueError("X=%d is not in range" % x)
        return yp


def test_arima():
    import matplotlib.pyplot as plt
    n = 200
    noise = 1.0
    X = np.arange(0, n, dtype=int).reshape((n, 1))
    y = np.sin(0.3 * X) + noise * np.random.rand(n, 1) + 0.2 * X
    X_tr = X[:120]
    y_tr = y[:120]
    model = Arima(rank=7, alpha=0.1)
    model.fit(X_tr, y_tr)
    yp = model.predict(X)
    plt.figure()
    plt.plot(X, y, ".")
    plt.plot(X, yp, "-", color="red")
    plt.show()


if __name__ == "__main__":
    test_arima()
