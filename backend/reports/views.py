from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from verification import assistant
from verification.serializers import AskSerializer

from . import integrity
from .models import Report
from .services import serialize_report


class AskThrottle(AnonRateThrottle):
    rate = "20/minute"


@api_view(["GET"])
def report_detail(request, public_id):
    report = get_object_or_404(Report, public_id=public_id.upper())
    return Response(serialize_report(report, request))


@api_view(["GET"])
def report_verify(request, public_id):
    report = Report.objects.filter(public_id=public_id.upper()).first()
    if not report:
        return Response({"authentic": False, "reason": "not_found"})
    outcome = integrity.check(report, request.query_params.get("h", ""))
    result = report.result
    return Response({
        **outcome,
        "id": report.public_id,
        "created_at": report.created_at.isoformat(),
        "sha256": report.sha256,
        "facts": {
            "plot": result["plot"],
            "seller": result["seller"]["name"],
            "area_acre": result["input"]["area_acre"],
            "score": result["score"],
            "level": result["level"],
            "flags": [f["title"] for f in result["flags"]],
        },
    })


@api_view(["POST"])
@throttle_classes([AskThrottle])
def report_ask(request, public_id):
    report = get_object_or_404(Report, public_id=public_id.upper())
    s = AskSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    return Response(assistant.answer(s.validated_data["question"], report.result, s.validated_data["lang"]))
