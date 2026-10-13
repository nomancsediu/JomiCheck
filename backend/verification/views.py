from decimal import Decimal
from fractions import Fraction

from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from reports.services import create_report, serialize_report

from . import faraiz
from .engine import PlotNotFound, verify
from .serializers import InheritanceRequestSerializer, VerifyRequestSerializer


class VerifyThrottle(AnonRateThrottle):
    rate = "30/minute"


@api_view(["POST"])
@throttle_classes([VerifyThrottle])
def verify_plot(request):
    s = VerifyRequestSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    data = s.validated_data
    try:
        result = verify(
            data["mouza_id"], data["dag_no"], data["seller_name"], data["area_acre"],
            data["khatian_no"], data["buyer_token"],
        )
    except PlotNotFound:
        return Response(
            {"detail": "Dag not found in the selected mouza.", "detail_bn": "নির্বাচিত মৌজায় এই দাগ পাওয়া যায়নি।"},
            status=status.HTTP_404_NOT_FOUND,
        )
    report = create_report(result)
    return Response(serialize_report(report), status=status.HTTP_201_CREATED)


@api_view(["POST"])
def inheritance(request):
    s = InheritanceRequestSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    area = Fraction(str(s.validated_data["area_acre"]))
    heirs = [
        faraiz.Heir(key=str(i), relation=h["relation"], name=h["name"])
        for i, h in enumerate(s.validated_data["heirs"])
    ]
    try:
        result = faraiz.calculate(heirs)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        "area_acre": str(s.validated_data["area_acre"].normalize()),
        "heirs": [{
            "name": sh.name, "relation": sh.relation,
            "share": f"{sh.share.numerator}/{sh.share.denominator}",
            "share_decimal": round(float(sh.share), 6),
            "area_acre": f"{Decimal(float(sh.share * area)).quantize(Decimal('0.0001')).normalize():f}",
            "basis": sh.basis,
        } for sh in result.shares],
        "notes": result.notes,
        "law": "Muslim personal law (Faraiz)",
    })
