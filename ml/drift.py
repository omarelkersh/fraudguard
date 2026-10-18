import numpy as np


def psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index: how much `current` has shifted away from `reference`."""
    edges = np.unique(
        np.quantile(reference, np.linspace(0, 1, bins + 1))
    )  # bucket borders from training data
    edges[0], edges[-1] = -np.inf, np.inf  # catch values outside the range
    ref_pct = np.histogram(reference, edges)[0] / len(reference)
    cur_pct = np.histogram(current, edges)[0] / len(current)
    ref_pct, cur_pct = np.clip(ref_pct, 1e-6, None), np.clip(cur_pct, 1e-6, None)  # avoid log(0)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
