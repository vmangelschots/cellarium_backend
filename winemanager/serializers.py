from rest_framework import serializers
from .models import Wine, Bottle, Store

class WineSerializer(serializers.ModelSerializer):
    bottle_count = serializers.IntegerField(read_only=True)
    in_stock_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Wine
        fields = [
            "id",
            "name",
            "region",
            "country",
            "vintage",
            "grape_varieties",
            "wine_type",
            "notes",
            "bottle_count",
            "in_stock_count",
        ]
class BottleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bottle
        fields = '__all__'

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__' 