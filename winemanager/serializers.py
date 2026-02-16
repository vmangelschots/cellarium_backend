from rest_framework import serializers
from django_countries.serializers import CountryFieldMixin
from .models import Wine, Bottle, Store, Region

class RegionSerializer(CountryFieldMixin, serializers.ModelSerializer):
    wine_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Region
        fields = ['id', 'name', 'country', 'wine_count']

class WineSerializer(CountryFieldMixin, serializers.ModelSerializer):
    bottle_count = serializers.IntegerField(read_only=True)
    in_stock_count = serializers.IntegerField(read_only=True)
    region_details = RegionSerializer(source='region', read_only=True)
    
    class Meta:
        model = Wine
        fields = [
            "id",
            "name",
            "region",
            "region_details",
            "country",
            "vintage",
            "grape_varieties",
            "wine_type",
            "notes",
            "image",
            "bottle_count",
            "in_stock_count",
            "rating",
            "poy",
        ]
    
    def validate_rating(self, value):
        if value is not None and (value < 0.0 or value > 5.0):
            raise serializers.ValidationError("Rating must be between 0.0 and 5.0")
        return value
    
    def to_representation(self, instance):
        """Custom representation to show nested region details"""
        representation = super().to_representation(instance)
        # For reading, show full region object; for writing, accept just region ID
        if instance.region:
            representation['region'] = RegionSerializer(instance.region).data
        return representation
    
class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__' 
class BottleSerializer(serializers.ModelSerializer):
    store_details = StoreSerializer(source='store', read_only=True)
    class Meta:
        model = Bottle
        fields = '__all__'
    
    def to_representation(self, instance):
        """Custom representation to show nested store details"""
        representation = super().to_representation(instance)
        # Replace store ID with nested store object for reading
        if instance.store:
            representation['store'] = StoreSerializer(instance.store).data
        return representation

