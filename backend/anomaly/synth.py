"""
Synthetic land-transfer data for training and evaluating the anomaly model.

Normal transfers follow a plausible rural/peri-urban market: most land is held
for years, sells above the government mouza rate and changes hands rarely.
A small share of transfers follow known fraud patterns. Labels are kept only
for evaluation; the model itself trains without them.
"""
import numpy as np

from .features import MAX_HOLDING_DAYS

PATTERNS = {
    "flip": "Bought and resold within months at a low price",
    "broker": "One seller selling many plots within a year",
    "chain": "The same plot changing hands repeatedly within a year",
    "undervalue": "Price far below the government mouza rate",
}


def _normal(rng: np.random.Generator, n: int) -> np.ndarray:
    price = np.clip(rng.lognormal(np.log(1.4), 0.3, n), 0.6, 5)
    holding = np.clip(rng.lognormal(np.log(3300), 0.8, n), 60, MAX_HOLDING_DAYS)
    transfers = 1 + rng.choice([0, 1, 2], n, p=[0.91, 0.08, 0.01])
    whole = rng.random(n) < 0.4
    area = np.where(whole, 1.0, rng.uniform(0.1, 0.95, n))
    seller_plots = 1 + rng.choice([0, 1, 2], n, p=[0.92, 0.07, 0.01])
    return np.column_stack([price, np.log1p(holding), transfers, area, seller_plots])


def _anomalies(rng: np.random.Generator, n: int) -> tuple[np.ndarray, list[str]]:
    X = _normal(rng, n)
    kinds = rng.choice(list(PATTERNS), n)
    for i, kind in enumerate(kinds):
        if kind == "flip":
            X[i, 0] = rng.uniform(0.5, 1.0)
            X[i, 1] = np.log1p(rng.uniform(20, 200))
            X[i, 2] = rng.integers(2, 4)
        elif kind == "broker":
            X[i, 1] = np.log1p(rng.uniform(30, 400))
            X[i, 4] = rng.integers(3, 9)
        elif kind == "chain":
            X[i, 1] = np.log1p(rng.uniform(30, 150))
            X[i, 2] = rng.integers(3, 7)
        else:
            X[i, 0] = rng.uniform(0.25, 0.6)
    return X, list(kinds)


def generate(n: int, anomaly_rate: float, seed: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Return features, labels (1 = anomaly) and the pattern name per row ("normal" for normal rows)."""
    rng = np.random.default_rng(seed)
    n_bad = int(n * anomaly_rate)
    good = _normal(rng, n - n_bad)
    bad, kinds = _anomalies(rng, n_bad)
    X = np.vstack([good, bad])
    y = np.concatenate([np.zeros(len(good), dtype=int), np.ones(n_bad, dtype=int)])
    patterns = ["normal"] * len(good) + kinds
    order = rng.permutation(len(X))
    return X[order], y[order], [patterns[i] for i in order]
