from django.test import TestCase
from rest_framework.test import APIClient

from land.models import Mouza
from land.seed import seed

from .models import Report


class ApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed(nationwide=False)

    def setUp(self):
        self.client = APIClient()
        self.rampur = Mouza.objects.get(name_en="Rampur")

    def _verify(self, **overrides):
        payload = {"mouza_id": self.rampur.id, "dag_no": "125", "seller_name": "Rahim Uddin",
                   "area_acre": "0.30", "khatian_no": "456", **overrides}
        return self.client.post("/api/verify/", payload, format="json")

    def test_locations_and_demo_cases(self):
        locs = self.client.get("/api/locations/").json()
        self.assertEqual({d["name"]["en"] for d in locs}, {"Dhaka", "Gazipur"})
        cases = self.client.get("/api/demo-cases/").json()
        self.assertEqual(len(cases), 14)
        self.assertIn("mouza_id", cases[0])

    def test_verify_creates_sealed_report(self):
        res = self._verify()
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body["result"]["level"], "HIGH")
        self.assertEqual(body["result"]["score"], 91)
        self.assertEqual(len(body["sha256"]), 64)
        self.assertIn("<svg", body["qr_svg"])

    def test_verify_unknown_dag_returns_404(self):
        self.assertEqual(self._verify(dag_no="99999").status_code, 404)

    def test_verify_rejects_bad_area(self):
        self.assertEqual(self._verify(area_acre="0").status_code, 400)

    def test_report_verification_detects_tampering(self):
        body = self._verify().json()
        ok = self.client.get(f"/api/reports/{body['id']}/verify/?h={body['sha256']}").json()
        self.assertTrue(ok["authentic"])

        wrong = self.client.get(f"/api/reports/{body['id']}/verify/?h={'0' * 64}").json()
        self.assertFalse(wrong["authentic"])

        report = Report.objects.get(public_id=body["id"])
        report.result["score"] = 5
        report.save()
        edited = self.client.get(f"/api/reports/{body['id']}/verify/?h={body['sha256']}").json()
        self.assertEqual(edited["reason"], "registry_record_modified")

    def test_ask_uses_builtin_assistant(self):
        body = self._verify().json()
        res = self.client.post(f"/api/reports/{body['id']}/ask/", {"question": "হক-শুফা কী?", "lang": "bn"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["source"], "built-in")
        self.assertIn("শরিক", res.json()["answer"])

    def test_inheritance_calculator_endpoint(self):
        res = self.client.post("/api/inheritance/", {
            "area_acre": "1.00",
            "heirs": [{"relation": "wife"}, {"relation": "son"}, {"relation": "son"}, {"relation": "daughter"}],
        }, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([h["share"] for h in res.json()["heirs"]], ["1/8", "7/20", "7/20", "7/40"])
