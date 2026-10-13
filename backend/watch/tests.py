import io

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from land.models import Mouza, Plot
from land.seed import seed
from verification.engine import verify


class WatchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.plot = Plot.objects.get(mouza__name_en="Rampur", dag_no="101")

    def setUp(self):
        self.client = APIClient()

    def start(self, token="buyer-a"):
        return self.client.post("/api/watch/", {"plot_id": self.plot.id, "buyer_token": token, "report_id": "ABC"},
                                format="json")

    def listed(self, token="buyer-a"):
        return self.client.get("/api/watch/", {"buyer_token": token}).json()

    def test_no_alerts_right_after_watching(self):
        self.assertEqual(self.start().status_code, 201)
        self.assertEqual(self.start().json()["id"], self.listed()[0]["id"])  # watching twice keeps one watch
        self.assertEqual(self.listed()[0]["alerts"], [])

    def test_new_records_and_other_buyers_raise_alerts(self):
        self.start()
        call_command("simulate_watch_event", "101", kind="injunction", stdout=io.StringIO())
        call_command("simulate_watch_event", "101", kind="mortgage", stdout=io.StringIO())
        verify(Mouza.objects.get(name_en="Rampur").id, "101", "Jamal Hossain", "0.33", buyer_token="buyer-b")
        alerts = self.listed()[0]["alerts"]
        self.assertEqual([a["kind"] for a in alerts], ["legal", "mortgage", "buyer"])
        self.assertEqual(alerts[0]["severity"], "critical")
        self.assertIn("নিষেধাজ্ঞা", alerts[0]["bn"])

    def test_watches_are_private_to_the_buyer(self):
        watch_id = self.start().json()["id"]
        self.assertEqual(self.listed("buyer-b"), [])
        self.assertEqual(self.client.delete(f"/api/watch/{watch_id}/?buyer_token=buyer-b").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/watch/{watch_id}/?buyer_token=buyer-a").status_code, 204)
        self.assertEqual(self.listed(), [])

    def test_token_and_plot_are_required(self):
        self.assertEqual(self.client.get("/api/watch/").status_code, 400)
        res = self.client.post("/api/watch/", {"plot_id": 999999, "buyer_token": "x"}, format="json")
        self.assertEqual(res.status_code, 404)
