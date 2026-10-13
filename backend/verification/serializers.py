from decimal import Decimal

from rest_framework import serializers

from .faraiz import RELATIONS


class VerifyRequestSerializer(serializers.Serializer):
    mouza_id = serializers.IntegerField(min_value=1)
    dag_no = serializers.CharField(max_length=20)
    seller_name = serializers.CharField(max_length=120)
    area_acre = serializers.DecimalField(max_digits=8, decimal_places=4, min_value=Decimal("0.0001"))
    khatian_no = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    buyer_token = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    # Fields of uploaded documents as returned by /api/documents/extract/, checked against the records.
    documents = serializers.ListField(child=serializers.DictField(), required=False, default=list, max_length=5)


class HeirInputSerializer(serializers.Serializer):
    relation = serializers.ChoiceField(choices=RELATIONS)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")


class InheritanceRequestSerializer(serializers.Serializer):
    area_acre = serializers.DecimalField(max_digits=8, decimal_places=4, min_value=Decimal("0.0001"))
    heirs = HeirInputSerializer(many=True, allow_empty=False)


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)
    lang = serializers.ChoiceField(choices=["bn", "en"], default="bn")
