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
            "alcohol_percentage",
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


# Serializers for wine label analysis response
class MatchedRegionSerializer(serializers.Serializer):
    """Serializer for a fuzzy-matched region from the database."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    country = serializers.CharField()
    match_score = serializers.FloatField(help_text="Fuzzy match score between 0.0 and 1.0")


class LabelAnalysisDataSerializer(serializers.Serializer):
    """Serializer for extracted wine data from label analysis."""
    name = serializers.CharField(allow_null=True, required=False)
    vintage = serializers.IntegerField(allow_null=True, required=False)
    wine_type = serializers.ChoiceField(
        choices=["red", "white", "rosé", "sparkling"],
        allow_null=True,
        required=False
    )
    country = serializers.CharField(allow_null=True, required=False, help_text="ISO 3166-1 alpha-2 code")
    grape_varieties = serializers.CharField(allow_null=True, required=False)
    alcohol_percentage = serializers.FloatField(allow_null=True, required=False)
    suggested_region_name = serializers.CharField(allow_null=True, required=False)
    matched_region = MatchedRegionSerializer(allow_null=True, required=False)


class LabelAnalysisConfidenceSerializer(serializers.Serializer):
    """Serializer for confidence scores per field."""
    name = serializers.FloatField(default=0.0)
    vintage = serializers.FloatField(default=0.0)
    wine_type = serializers.FloatField(default=0.0)
    country = serializers.FloatField(default=0.0)
    region = serializers.FloatField(default=0.0)
    grape_varieties = serializers.FloatField(default=0.0)
    alcohol_percentage = serializers.FloatField(default=0.0)


class LabelAnalysisResponseSerializer(serializers.Serializer):
    """Main response serializer for wine label analysis."""
    success = serializers.BooleanField()
    data = LabelAnalysisDataSerializer()
    confidence = LabelAnalysisConfidenceSerializer()
    raw_text = serializers.CharField(allow_blank=True, help_text="All text extracted from the label")


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

