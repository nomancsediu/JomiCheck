from decimal import Decimal

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from .calculator import estimate


class EstimateTests(SimpleTestCase):
    def test_union_area_breakdown(self):
        r = estimate(1_000_000, "union")
        amounts = {line["key"]: line["amount"] for line in r["registration"]}
        self.assertEqual(amounts, {"stamp_duty": 30_000, "registration_fee": 10_000,
                                   "local_gov_tax": 10_000, "source_tax": 20_000})
        self.assertEqual(r["mutation_total"], 1_200)
        self.assertEqual(r["grand_total"], 1_000_000 + 70_000 + 1_200)

    def test_major_city_rates(self):
        amounts = {line["key"]: line["amount"] for line in estimate(1_000_000, "city_major")["registration"]}
        self.assertEqual(amounts["local_gov_tax"], 30_000)
        self.assertEqual(amounts["source_tax"], 40_000)

    def test_price_below_mouza_minimum_uses_minimum(self):
        r = estimate(500_000, "pourashava", area_acre=Decimal("0.5"), mouza_rate_per_acre=2_000_000)
        self.assertTrue(r["below_minimum"])
        self.assertEqual(r["mouza_minimum_bdt"], 1_000_000)
        self.assertEqual(r["deed_value_bdt"], 1_000_000)
        self.assertIn("minimum", r["notes"][0]["en"])

    def test_unknown_area_type(self):
        with self.assertRaises(ValueError):
            estimate(100, "mars")


class EstimateApiTests(SimpleTestCase):
    def test_endpoint(self):
        res = APIClient().post("/api/costs/estimate/", {"price_bdt": 1_000_000, "area_type": "union"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["registration_total"], 70_000)

    def test_rejects_bad_area_type(self):
        res = APIClient().post("/api/costs/estimate/", {"price_bdt": 1, "area_type": "mars"}, format="json")
        self.assertEqual(res.status_code, 400)
