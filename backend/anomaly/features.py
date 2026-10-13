"""
Features describing one land transfer, used by the anomaly model.

The same definitions are used for the synthetic training data (synth.py) and
for real records at verification time, so the model sees comparable numbers.
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from land import models as m

FEATURES = ["price_ratio", "log_holding_days", "plot_transfers_365", "area_fraction", "seller_plots_365"]

# Used for a proposed sale, whose price is not known yet.
NEUTRAL_PRICE_RATIO = 1.4
MAX_HOLDING_DAYS = 30 * 365
UNKNOWN_HOLDING_DAYS = 10 * 365


@dataclass
class Transfer:
    """A sale to score: either a registered deed or the sale the buyer is considering."""
    label: str
    when: date
    holding_days: int
    price_ratio: float
    plot_transfers_365: int
    area_fraction: float
    seller_plots_365: int

    def vector(self) -> list[float]:
        return [
            self.price_ratio,
            math.log1p(min(max(self.holding_days, 0), MAX_HOLDING_DAYS)),
            float(self.plot_transfers_365),
            self.area_fraction,
            float(self.seller_plots_365),
        ]


def acquired_on(person: m.Person, plot: m.Plot, before: date) -> date | None:
    """When the person got their right in this plot: by deed, inheritance or the record of rights."""
    bought = (m.Deed.objects.filter(plot=plot, buyers=person, status=m.Deed.Status.REGISTERED,
                                    registration_date__lt=before)
              .order_by("-registration_date").values_list("registration_date", flat=True).first())
    if bought:
        return bought
    link = m.HeirLink.objects.filter(heir=person, deceased__date_of_death__isnull=False,
                                     deceased__khatian_shares__khatian__plots=plot).select_related("deceased").first()
    if link and link.deceased.date_of_death < before:
        return link.deceased.date_of_death
    year = (m.KhatianOwner.objects.filter(person=person, khatian__plots=plot)
            .order_by("khatian__record_year").values_list("khatian__record_year", flat=True).first())
    return date(year, 1, 1) if year else None


def _holding_days(sellers, plot, when) -> int:
    days = []
    for s in sellers:
        start = acquired_on(s, plot, when)
        days.append((when - start).days if start else UNKNOWN_HOLDING_DAYS)
    return min(days) if days else UNKNOWN_HOLDING_DAYS


def _sales_window(when: date):
    return m.Deed.objects.filter(
        deed_type=m.Deed.DeedType.SALE, status=m.Deed.Status.REGISTERED,
        registration_date__gt=when - timedelta(days=365), registration_date__lte=when,
    )


def _seller_plots(sellers, when, extra_plot=None) -> int:
    plots = set(_sales_window(when).filter(sellers__in=sellers).values_list("plot_id", flat=True))
    if extra_plot is not None:
        plots.add(extra_plot.id)
    return len(plots)


def deed_transfer(deed: m.Deed) -> Transfer:
    plot = deed.plot
    sellers = list(deed.sellers.all())
    value = Decimal(plot.mouza_rate_per_acre) * deed.area_acre
    return Transfer(
        label=f"Deed {deed.deed_no}",
        when=deed.registration_date,
        holding_days=_holding_days(sellers, plot, deed.registration_date),
        price_ratio=float(Decimal(deed.price_bdt) / value) if value else NEUTRAL_PRICE_RATIO,
        plot_transfers_365=_sales_window(deed.registration_date).filter(plot=plot).count(),
        area_fraction=float(deed.area_acre / plot.area_acre),
        seller_plots_365=_seller_plots(sellers, deed.registration_date),
    )


def proposed_transfer(seller: m.Person, plot: m.Plot, area_acre: Decimal, today: date) -> Transfer:
    return Transfer(
        label="Proposed sale",
        when=today,
        holding_days=_holding_days([seller], plot, today),
        price_ratio=NEUTRAL_PRICE_RATIO,
        plot_transfers_365=_sales_window(today).filter(plot=plot).count() + 1,
        area_fraction=float(min(area_acre / plot.area_acre, Decimal(1))),
        seller_plots_365=_seller_plots([seller], today, extra_plot=plot),
    )
