from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import rates
from .calculator import estimate


class EstimateRequestSerializer(serializers.Serializer):
    price_bdt = serializers.IntegerField(min_value=0, max_value=10**12)
    area_type = serializers.ChoiceField(choices=list(rates.AREA_TYPES))
    area_acre = serializers.DecimalField(max_digits=10, decimal_places=4, min_value=0, required=False)
    mouza_rate_per_acre = serializers.IntegerField(min_value=0, required=False)


@api_view(["POST"])
def cost_estimate(request):
    s = EstimateRequestSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data
    return Response(estimate(d["price_bdt"], d["area_type"], d.get("area_acre"), d.get("mouza_rate_per_acre")))
