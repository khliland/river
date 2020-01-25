import collections

from . import base


class RandomUnderSampler(base.Sampler):
    """Random under-sampling.

    This is a wrapper for classifiers. It will train the provided classifier by under-sampling the
    stream of given observations so that the class distribution seen by the classifier follows
    a given desired distribution. The implementation is a discrete version of rejection sampling.

    Parameters:
        classifier (base.Classifier)
        desired_dist (dict): The desired class distribution. The keys are the classes whilst the
            values are the desired class percentages. The values must sum up to 1.

    See :ref:`Working with imbalanced data` for example usage.

    References:
        1. `Under-sampling a dataset with desired ratios <https://maxhalford.github.io/blog/under-sampling-a-dataset-with-desired-ratios/>`_
        2. `Wikipedia article on rejection sampling <https://www.wikiwand.com/en/Rejection_sampling>`_

    """

    def __init__(self, classifier, desired_dist, seed=None):
        super().__init__(classifier=classifier, seed=seed)
        self.desired_dist = desired_dist
        self._actual_dist = collections.Counter()
        self._pivot = None

    def fit_one(self, x, y):

        self._actual_dist[y] += 1
        f = self.desired_dist
        g = self._actual_dist

        # Check if the pivot needs to be changed
        if y != self._pivot:
            self._pivot = max(g.keys(), key=lambda y: f[y] / g[y])
        else:
            self.classifier.fit_one(x, y)
            return self

        # Determine the sampling ratio if the class is not the pivot
        M = f[self._pivot] / g[self._pivot]  # Likelihood ratio
        ratio = f[y] / (M * g[y])

        if ratio < 1 and self._rng.random() < ratio:
            self.classifier.fit_one(x, y)

        return self


class RandomOverSampler(base.Sampler):
    """Random over-sampling.

    This is a wrapper for classifiers. It will train the provided classifier by over-sampling the
    stream of given observations so that the class distribution seen by the classifier follows
    a given desired distribution. The implementation is a discrete version of reverse rejection
    sampling.

    Parameters:
        classifier (base.Classifier)
        desired_dist (dict): The desired class distribution. The keys are the classes whilst the
            values are the desired class percentages. The values must sum up to 1.

    See :ref:`Working with imbalanced data` for example usage.

    """

    def __init__(self, classifier, desired_dist, seed=None):
        super().__init__(classifier=classifier, seed=seed)
        self.desired_dist = desired_dist
        self._actual_dist = collections.Counter()
        self._pivot = None

    def fit_one(self, x, y):

        self._actual_dist[y] += 1
        f = self.desired_dist
        g = self._actual_dist

        # Check if the pivot needs to be changed
        if y != self._pivot:
            self._pivot = max(g.keys(), key=lambda y: g[y] / f[y])
        else:
            self.classifier.fit_one(x, y)
            return self

        M = g[self._pivot] / f[self._pivot]
        rate = M * f[y] / g[y]

        for _ in range(self._rng.poisson(rate)):
            self.classifier.fit_one(x, y)

        return self


class RandomSampler(base.Sampler):
    """Random sampling by mixing under-sampling and over-sampling.

    This is a wrapper for classifiers. It will train the provided classifier by both under-sampling
    and over-sampling the stream of given observations so that the class distribution seen by the
    classifier follows a given desired distribution.

    Parameters:
        classifier (base.Classifier)
        desired_dist (dict): The desired class distribution. The keys are the classes whilst the
            values are the desired class percentages. The values must sum up to 1.
        sampling_rate (float): The desired ratio of data to sample.

    See :ref:`Working with imbalanced data` for example usage.

    """

    def __init__(self, classifier, desired_dist, sampling_rate=1., seed=None):
        super().__init__(classifier=classifier, seed=seed)
        self.desired_dist = desired_dist
        self.sampling_rate = sampling_rate
        self._actual_dist = collections.Counter()
        self._n = 0

    def fit_one(self, x, y):

        self._actual_dist[y] += 1
        self._n += 1
        f = self.desired_dist
        g = self._actual_dist

        rate = self.sampling_rate * f[y] / (g[y] / self._n)

        for _ in range(self._rng.poisson(rate)):
            self.classifier.fit_one(x, y)

        return self
