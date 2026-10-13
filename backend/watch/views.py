from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from land.models import Plot

from .events import alerts, snapshot
from .models import PlotWatch


def _token(request) -> str:
    return str(request.data.get("buyer_token") or request.query_params.get("buyer_token") or "").strip()[:64]


def _serialize(w: PlotWatch) -> dict:
    p, mz = w.plot, w.plot.mouza
    return {
        "id": w.id,
        "plot_id": p.id,
        "report_id": w.report_id,
        "created_at": w.created_at.isoformat(),
        "plot": {
            "dag_no": p.dag_no,
            "mouza": {"en": mz.name_en, "bn": mz.name_bn},
            "upazila": {"en": mz.upazila.name_en, "bn": mz.upazila.name_bn},
        },
        "alerts": alerts(w),
    }


@api_view(["GET", "POST"])
def watches(request):
    token = _token(request)
    if not token:
        return Response({"detail": "buyer_token is required."}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == "POST":
        plot = Plot.objects.filter(pk=request.data.get("plot_id")).first()
        if not plot:
            return Response({"detail": "Plot not found."}, status=status.HTTP_404_NOT_FOUND)
        watch, _ = PlotWatch.objects.get_or_create(
            plot=plot, buyer_token=token,
            defaults={"snapshot": snapshot(plot), "report_id": str(request.data.get("report_id") or "")[:12]},
        )
        return Response(_serialize(watch), status=status.HTTP_201_CREATED)
    qs = PlotWatch.objects.filter(buyer_token=token).select_related("plot__mouza__upazila")
    return Response([_serialize(w) for w in qs])


@api_view(["DELETE"])
def stop_watching(request, watch_id: int):
    deleted, _ = PlotWatch.objects.filter(pk=watch_id, buyer_token=_token(request)).delete()
    return Response(status=status.HTTP_204_NO_CONTENT if deleted else status.HTTP_404_NOT_FOUND)
