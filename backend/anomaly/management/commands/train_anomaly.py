import json

from django.core.management.base import BaseCommand

from anomaly import model


class Command(BaseCommand):
    help = "Train the transfer anomaly model on synthetic data and report its evaluation metrics."

    def handle(self, *args, **opts):
        metrics = model.train()
        model.load.cache_clear()
        self.stdout.write(json.dumps(metrics, indent=2))
        self.stdout.write(self.style.SUCCESS(f"Saved {model.MODEL_PATH.relative_to(model.ARTIFACT_DIR.parent.parent)}"))
