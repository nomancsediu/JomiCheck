from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import mapsheet
from .models import District, Mouza
from .seed import DEMO_CASES


@api_view(["GET"])
def locations(request):
    data = []
    for d in District.objects.prefetch_related("upazilas__mouzas"):
        data.append({
            "id": d.id, "name": {"en": d.name_en, "bn": d.name_bn},
            "upazilas": [{
                "id": u.id, "name": {"en": u.name_en, "bn": u.name_bn},
                "mouzas": [{"id": mz.id, "name": {"en": mz.name_en, "bn": mz.name_bn}, "jl_no": mz.jl_no}
                           for mz in u.mouzas.all()],
            } for u in d.upazilas.all()],
        })
    return Response(data)


@api_view(["GET"])
def mouza_plots(request, mouza_id):
    mouza = get_object_or_404(Mouza, pk=mouza_id)
    return Response([
        {"dag_no": p.dag_no, "area_acre": str(p.area_acre.normalize())}
        for p in mouza.plots.order_by("dag_no")
    ])


@api_view(["GET"])
def mouza_map(request, mouza_id):
    return Response(mapsheet.build(get_object_or_404(Mouza, pk=mouza_id)))


@api_view(["GET"])
def demo_cases(request):
    mouzas = {mz.name_en: mz for mz in Mouza.objects.select_related("upazila__district")}
    cases = []
    for case in DEMO_CASES:
        mz = mouzas.get(case["mouza"])
        if not mz:
            continue
        cases.append({
            **case,
            "mouza_bn": mz.name_bn,
            "district_id": mz.upazila.district_id,
            "upazila_id": mz.upazila_id,
            "mouza_id": mz.id,
        })
    return Response(cases)
