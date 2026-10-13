"""Add a synthetic new record to a plot so the watch alerts can be demonstrated."""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from land import models as m

KINDS = ["injunction", "mortgage", "bainanama"]


class Command(BaseCommand):
    help = "Record a synthetic injunction, mortgage or bainanama on a plot (demo only)."

    def add_arguments(self, parser):
        parser.add_argument("dag_no")
        parser.add_argument("--mouza", default="Rampur")
        parser.add_argument("--kind", choices=KINDS, default="injunction")
        parser.add_argument("--clear", action="store_true", help="Remove every demo event from this plot instead.")

    def handle(self, *args, dag_no, mouza, kind, clear, **opts):
        plot = m.Plot.objects.filter(mouza__name_en=mouza, dag_no=dag_no).first()
        if not plot:
            raise CommandError(f"Dag {dag_no} not found in {mouza}.")
        if clear:
            removed = (
                m.LegalStatus.objects.filter(plot=plot, reference_no__endswith="(demo)").delete()[0]
                + m.Mortgage.objects.filter(plot=plot, lender="Demo Krishi Bank").delete()[0]
                + m.Bainanama.objects.filter(plot=plot, buyer__nid="0000009999").delete()[0]
            )
            self.stdout.write(self.style.SUCCESS(f"Removed {removed} demo event(s) from dag {dag_no}, {mouza}."))
            return
        owner = max(plot.khatians.all(), key=lambda k: k.order).owners.first().person
        today = date.today()
        if kind == "injunction":
            m.LegalStatus.objects.create(
                plot=plot, status_type="injunction", reference_no=f"Title Suit {today.day:02d}/{today.year} (demo)",
                description="Temporary injunction on transfer (synthetic demo event)", since=today,
            )
        elif kind == "mortgage":
            m.Mortgage.objects.create(plot=plot, mortgagor=owner, lender="Demo Krishi Bank", amount_bdt=500_000,
                                      registered_on=today)
        else:
            buyer, _ = m.Person.objects.get_or_create(nid="0000009999", defaults={"name_en": "Demo Buyer", "name_bn": "ডেমো ক্রেতা"})
            m.Bainanama.objects.create(
                agreement_no=f"BN-{today:%Y%m%d}-{m.Bainanama.objects.count() + 1}", plot=plot, seller=owner,
                buyer=buyer, area_acre=plot.area_acre, agreement_date=today,
            )
        self.stdout.write(self.style.SUCCESS(f"Recorded a synthetic {kind} on dag {dag_no}, {mouza}."))
