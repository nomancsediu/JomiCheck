import json
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from verification.assistant import chat


class Command(BaseCommand):
    help = "Check the report-assistant LLM connection, or list the models the API key can use."

    def add_arguments(self, parser):
        parser.add_argument("--list", action="store_true", help="List available models (Gemma models only, unless --all).")
        parser.add_argument("--all", action="store_true", help="With --list, show every model.")

    def handle(self, *args, **opts):
        if not settings.LLM_API_URL or not settings.LLM_API_KEY:
            raise CommandError("Set LLM_API_URL and LLM_API_KEY in backend/.env first (see backend/.env.example).")

        if opts["list"]:
            req = urllib.request.Request(
                settings.LLM_API_URL.rstrip("/") + "/models",
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
            )
            try:
                with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT) as resp:
                    models = [m["id"].removeprefix("models/") for m in json.loads(resp.read())["data"]]
            except urllib.error.HTTPError as exc:
                raise CommandError(f"HTTP {exc.code}: {exc.read().decode()[:300]}") from exc
            for model in sorted(models):
                if opts["all"] or "gemma" in model.lower():
                    self.stdout.write(model)
            return

        if not settings.LLM_MODEL:
            raise CommandError("Set LLM_MODEL in backend/.env.")
        self.stdout.write(f"Model: {settings.LLM_MODEL}")
        start = time.monotonic()
        try:
            reply = chat(
                "You are a Bangladeshi land-law assistant. Answer in simple Bangla in one sentence.",
                "নামজারি কী?",
            )
        except urllib.error.HTTPError as exc:
            raise CommandError(f"HTTP {exc.code}: {exc.read().decode()[:300]}") from exc
        self.stdout.write(self.style.SUCCESS(f"OK in {time.monotonic() - start:.1f}s"))
        self.stdout.write(reply)
