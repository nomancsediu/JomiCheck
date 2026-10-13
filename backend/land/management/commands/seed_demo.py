from django.core.management.base import BaseCommand

from land.seed import seed


class Command(BaseCommand):
    help = "Wipe land records and load the synthetic demo dataset (fictional data only)."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Random seed for background plots")

    def handle(self, *args, **options):
        counts = seed(options["seed"])
        for name, value in counts.items():
            self.stdout.write(f"  {name:<18} {value}")
        self.stdout.write(self.style.SUCCESS("Synthetic dataset loaded."))
