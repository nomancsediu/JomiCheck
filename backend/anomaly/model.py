"""
Isolation Forest over land-transfer features.

The model only adds a statistical signal; the rule engine still decides the risk.
"""
import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_fscore_support

from . import synth
from .features import FEATURES, Transfer

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "transfer_iforest.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"

TRAIN_SIZE = 20_000
TEST_SIZE = 5_000
ANOMALY_RATE = 0.05
SEED = 42

# Feature -> direction that counts as unusual (-1: too low, +1: too high).
DIRECTIONS = {"price_ratio": -1, "log_holding_days": -1, "plot_transfers_365": 1, "seller_plots_365": 1}


def train() -> dict:
    X_train, _, _ = synth.generate(TRAIN_SIZE, ANOMALY_RATE, SEED)
    X_test, y_test, patterns = synth.generate(TEST_SIZE, ANOMALY_RATE, SEED + 1)

    model = IsolationForest(n_estimators=300, contamination=ANOMALY_RATE, random_state=SEED)
    model.fit(X_train)

    pred = (model.predict(X_test) == -1).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, pred, average="binary")
    per_pattern = {}
    for name in synth.PATTERNS:
        idx = [i for i, p in enumerate(patterns) if p == name]
        per_pattern[name] = round(float(pred[idx].mean()), 3) if idx else None
    normal_idx = [i for i, p in enumerate(patterns) if p == "normal"]

    normal_train = X_train[model.predict(X_train) == 1]
    bundle = {
        "model": model,
        "features": FEATURES,
        "p02": np.percentile(normal_train, 2, axis=0).tolist(),
        "p98": np.percentile(normal_train, 98, axis=0).tolist(),
    }
    metrics = {
        "model": "IsolationForest(n_estimators=300, contamination=0.05)",
        "features": FEATURES,
        "train_rows": TRAIN_SIZE, "test_rows": TEST_SIZE, "anomaly_rate": ANOMALY_RATE,
        "precision": round(float(precision), 3),
        "recall": round(float(recall), 3),
        "f1": round(float(f1), 3),
        "false_positive_rate": round(float(pred[normal_idx].mean()), 3),
        "recall_by_pattern": per_pattern,
        "note": "Measured on synthetic data with planted patterns; real-world accuracy needs real records.",
    }
    ARTIFACT_DIR.mkdir(exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


@lru_cache(maxsize=1)
def load() -> dict:
    """Load the trained model, training it first if the artifact is missing (takes a few seconds)."""
    if not MODEL_PATH.exists():
        train()
    return joblib.load(MODEL_PATH)


def _reasons(t: Transfer, vec: list[float], bundle: dict) -> list[dict]:
    out = []
    for i, name in enumerate(bundle["features"]):
        direction = DIRECTIONS.get(name)
        if direction == -1 and vec[i] < bundle["p02"][i] or direction == 1 and vec[i] > bundle["p98"][i]:
            out.append(name)
    texts = {
        "price_ratio": (f"price was {t.price_ratio:.0%} of the mouza value",
                        f"দাম মৌজা মূল্যের {t.price_ratio:.0%}"),
        "log_holding_days": (f"seller had held the land for only {t.holding_days} days",
                             f"বিক্রেতা মাত্র {t.holding_days} দিন জমির মালিক ছিলেন"),
        "plot_transfers_365": (f"{t.plot_transfers_365} sales of this dag within a year",
                               f"এক বছরে এই দাগে {t.plot_transfers_365}টি বিক্রি"),
        "seller_plots_365": (f"seller sold {t.seller_plots_365} different dags within a year",
                             f"বিক্রেতা এক বছরে {t.seller_plots_365}টি ভিন্ন দাগ বিক্রি করেছেন"),
    }
    return [{"feature": n, "en": texts[n][0], "bn": texts[n][1]} for n in out]


def score(transfers: list[Transfer]) -> list[dict]:
    """Score transfers; returns one entry per transfer with is_anomaly, score and reasons."""
    if not transfers:
        return []
    bundle = load()
    X = np.array([t.vector() for t in transfers])
    scores = bundle["model"].decision_function(X)
    results = []
    for t, vec, s in zip(transfers, X.tolist(), scores):
        results.append({
            "transfer": t,
            "score": round(float(s), 4),
            "is_anomaly": bool(s < 0),
            "reasons": _reasons(t, vec, bundle) if s < 0 else [],
        })
    return results
