from datetime import date

from django.test import SimpleTestCase

from . import model, synth
from .features import Transfer


def transfer(**kw):
    base = dict(label="t", when=date(2026, 1, 1), holding_days=3000, price_ratio=1.4,
                plot_transfers_365=1, area_fraction=1.0, seller_plots_365=1)
    return Transfer(**{**base, **kw})


class SynthTests(SimpleTestCase):
    def test_shape_labels_and_patterns(self):
        X, y, patterns = synth.generate(1000, 0.05, seed=1)
        self.assertEqual(X.shape, (1000, 5))
        self.assertEqual(int(y.sum()), 50)
        self.assertEqual({p for p, label in zip(patterns, y) if label == 0}, {"normal"})


class ModelTests(SimpleTestCase):
    def test_typical_sale_is_normal(self):
        [r] = model.score([transfer()])
        self.assertFalse(r["is_anomaly"])
        self.assertEqual(r["reasons"], [])

    def test_quick_resale_by_busy_seller_is_flagged_with_reasons(self):
        [r] = model.score([transfer(holding_days=90, seller_plots_365=4, plot_transfers_365=2)])
        self.assertTrue(r["is_anomaly"])
        features = {reason["feature"] for reason in r["reasons"]}
        self.assertIn("log_holding_days", features)
        self.assertIn("seller_plots_365", features)

    def test_saved_metrics_meet_minimum_quality(self):
        import json
        model.load()
        metrics = json.loads(model.METRICS_PATH.read_text())
        self.assertGreaterEqual(metrics["recall_by_pattern"]["broker"], 0.9)
        self.assertLessEqual(metrics["false_positive_rate"], 0.03)
