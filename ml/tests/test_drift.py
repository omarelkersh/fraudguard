import numpy as np
from drift import psi

rng = np.random.default_rng(0)


def test_same_distribution_is_stable():
    reference = rng.normal(50, 10, 5000)
    assert psi(reference, rng.normal(50, 10, 5000)) < 0.1  # "stable" threshold


def test_shifted_distribution_is_drift():
    reference = rng.normal(50, 10, 5000)
    assert psi(reference, rng.normal(80, 10, 5000)) > 0.1  # "significant drift" threshold
