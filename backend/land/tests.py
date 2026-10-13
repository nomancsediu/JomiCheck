from decimal import Decimal
from fractions import Fraction

from django.test import SimpleTestCase, TestCase

from . import mapsheet
from .models import Mouza
from .seed import seed
from .units import share_to_ana


class ShareToAnaTests(SimpleTestCase):
    def test_whole_and_half(self):
        self.assertEqual(share_to_ana(1)["en"], "16 ana")
        self.assertEqual(share_to_ana(Decimal("0.5"))["bn"], "৮ আনা")

    def test_eighth_is_two_ana(self):
        self.assertEqual(share_to_ana(Fraction(1, 8))["en"], "2 ana")

    def test_third_uses_smaller_units(self):
        r = share_to_ana(Fraction(1, 3))
        self.assertEqual(r["en"], "5 ana 6 gonda 2 kora 2 kranti")
        self.assertTrue(r["exact"])

    def test_stored_six_decimal_third_is_treated_as_exact(self):
        self.assertTrue(share_to_ana(Decimal("0.333333"))["exact"])

    def test_inexact_share_is_marked_approximate(self):
        r = share_to_ana(Fraction(1, 7))
        self.assertTrue(r["en"].startswith("≈ "))
        self.assertFalse(r["exact"])


class MouzaMapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.mouza = Mouza.objects.get(name_en="Rampur")

    def test_every_dag_is_drawn_once_with_its_record_risk(self):
        sheet = mapsheet.build(self.mouza)
        dags = [p["dag_no"] for p in sheet["plots"]]
        self.assertEqual(sorted(dags), sorted(self.mouza.plots.values_list("dag_no", flat=True)))
        risk = {p["dag_no"]: p["level"] for p in sheet["plots"]}
        self.assertEqual(risk["101"], "LOW")
        self.assertEqual(risk["118"], "HIGH")

    def test_layout_is_stable_and_inside_the_sheet(self):
        first, second = mapsheet.build(self.mouza), mapsheet.build(self.mouza)
        self.assertEqual([p["points"] for p in first["plots"]], [p["points"] for p in second["plots"]])
        for plot in first["plots"]:
            for x, y in plot["points"]:
                self.assertTrue(0 <= x <= first["width"] and 0 <= y <= first["height"])

    def test_neighbouring_rows_share_their_boundary(self):
        mouza = Mouza.objects.get(name_en="Charabag")
        sheet = mapsheet.build(mouza)
        sizes = [len(row) for row in mapsheet._rows(list(mouza.plots.all()))]
        self.assertEqual(len(sizes), 3)
        middle_row = sheet["plots"][sizes[0]:sizes[0] + sizes[1]]
        last_row = sheet["plots"][sizes[0] + sizes[1]:]
        edge_above = sorted({tuple(pt) for p in middle_row for pt in p["points"] if pt[1] > p["label"][1]})
        top_edge = [pt for p in last_row for pt in p["points"] if pt[1] < p["label"][1]]
        self.assertTrue(top_edge)

        def y_above(x):
            for (x0, y0), (x1, y1) in zip(edge_above, edge_above[1:]):
                if x0 <= x <= x1 and x1 > x0:
                    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            return next(y for ex, y in edge_above if ex == x)

        for x, y in top_edge:
            self.assertAlmostEqual(y, y_above(x), delta=1)

    def test_map_endpoint(self):
        res = self.client.get(f"/api/mouzas/{self.mouza.id}/map/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("road", res.json())
