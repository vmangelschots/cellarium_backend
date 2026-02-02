from rest_framework import serializers
from django_countries.serializers import CountryFieldMixin
from .models import Wine, Bottle, Store

class WineSerializer(CountryFieldMixin, serializers.ModelSerializer):
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
            "image",
            "bottle_count",
            "in_stock_count",
            "rating",
        ]
    def validate_rating(self, value):
        if value is not None and (value < 0.0 or value > 5.0):
            raise serializers.ValidationError("Rating must be between 0.0 and 5.0")
        return value
    
class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__' 
class BottleSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    class Meta:
        model = Bottle
        fields = '__all__'

