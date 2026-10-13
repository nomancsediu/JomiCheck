"""Synthetic mouza map sheet (naksha): dag outlines plus the record risk of every dag.

The geometry is generated, not surveyed. It is deterministic per mouza so the same dag
always sits in the same place, neighbouring dags share their boundaries, and each dag's
size roughly follows its recorded area.
"""
import math
import random
from decimal import Decimal

from .models import Mouza, Plot

WIDTH, HEIGHT, MARGIN, ROAD = 1000, 620, 16, 34
STEP = 20


def _boundary(k: int, y: float, seed: int, flat: bool = False):
    if flat:
        return lambda x: y
    a, b = 1.3 * k + seed % 7, 0.7 * k + seed % 5
    return lambda x: y + 9 * math.sin(x / 140 + a) + 4 * math.sin(x / 45 + b)


def _edge(func, x0: float, x1: float):
    xs = [x0] + [x for x in range(int(x0) // STEP * STEP + STEP, int(x1), STEP) if x0 < x < x1] + [x1]
    return [[round(x, 1), round(func(x), 1)] for x in xs]


def _rows(plots: list[Plot]) -> list[list[Plot]]:
    count = len(plots)
    n_rows = 1 if count <= 3 else 2 if count <= 8 else 3
    per_row = math.ceil(count / n_rows)
    return [plots[i:i + per_row] for i in range(0, count, per_row)]


def record_risk(plot: Plot) -> dict:
    """Run the full engine as if the recorded owner were selling their whole share."""
    from verification.engine import Verifier

    khatians = sorted(plot.khatians.all(), key=lambda k: k.order)
    if not khatians:
        return {"level": "HIGH", "score": 100, "flags": []}
    owners = list(khatians[-1].owners.select_related("person"))
    living = [o for o in owners if not o.person.is_deceased] or owners
    seller = living[0]
    result = Verifier(plot, seller.person.name_en, Decimal(seller.share) * plot.area_acre).run()
    return {
        "level": result["level"],
        "score": result["score"],
        "flags": [f["title"] for f in result["flags"] if f["tier"] in ("CRITICAL", "MAJOR")][:3],
    }


def build(mouza: Mouza) -> dict:
    plots = sorted(mouza.plots.all(), key=lambda p: (len(p.dag_no), p.dag_no))
    rng = random.Random(mouza.pk * 7919)
    rows = _rows(plots)
    road_after = 0 if len(rows) > 1 else None

    usable = HEIGHT - 2 * MARGIN - (ROAD if road_after is not None else 0)
    weights = [sum(float(p.area_acre) ** 0.6 for p in row) for row in rows]
    heights = [usable * w / sum(weights) for w in weights]

    tops, bottoms, y = [], [], MARGIN
    for r in range(len(rows)):
        if r == 0:
            top = _boundary(r, y, mouza.pk, flat=True)
        elif r - 1 == road_after:
            top = (lambda prev: lambda x: prev(x) + ROAD)(bottoms[-1])
        else:
            top = bottoms[-1]
        y += heights[r]
        bottom = _boundary(r, y, mouza.pk, flat=r == len(rows) - 1)
        tops.append(top)
        bottoms.append(bottom)
        if r == road_after:
            y += ROAD

    road, road_label = None, None
    if road_after is not None:
        mid = WIDTH / 2
        road_label = [mid, round((bottoms[road_after](mid) + tops[road_after + 1](mid)) / 2, 1)]
        road = _edge(bottoms[road_after], MARGIN, WIDTH - MARGIN) + list(
            reversed(_edge(tops[road_after + 1], MARGIN, WIDTH - MARGIN))
        )

    out = []
    for r, row in enumerate(rows):
        weights = [float(p.area_acre) ** 0.6 for p in row]
        total = sum(weights)
        span = WIDTH - 2 * MARGIN
        cuts, acc = [MARGIN], MARGIN
        for w in weights[:-1]:
            acc += span * w / total
            cuts.append(acc)
        cuts.append(WIDTH - MARGIN)
        lean = [0] + [rng.uniform(-22, 22) for _ in cuts[1:-1]] + [0]
        for i, plot in enumerate(row):
            x0t, x1t = cuts[i] + lean[i], cuts[i + 1] + lean[i + 1]
            x0b, x1b = cuts[i] - lean[i], cuts[i + 1] - lean[i + 1]
            top_edge, bottom_edge = _edge(tops[r], x0t, x1t), _edge(bottoms[r], x0b, x1b)
            points = top_edge + list(reversed(bottom_edge))
            corners = [top_edge[0], top_edge[-1], bottom_edge[0], bottom_edge[-1]]
            out.append({
                "id": plot.id,
                "dag_no": plot.dag_no,
                "area_acre": str(plot.area_acre.normalize()),
                "land_class": plot.land_class,
                "points": points,
                "label": [round(sum(c[0] for c in corners) / 4, 1), round(sum(c[1] for c in corners) / 4, 1)],
                **record_risk(plot),
            })

    return {
        "mouza": {"id": mouza.id, "name": {"en": mouza.name_en, "bn": mouza.name_bn}, "jl_no": mouza.jl_no},
        "width": WIDTH,
        "height": HEIGHT,
        "road": road,
        "road_label": road_label,
        "plots": out,
    }
