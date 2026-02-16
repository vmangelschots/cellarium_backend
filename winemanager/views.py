from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from .models import Wine, Bottle, Store, Region
from .serializers import (
    WineSerializer, BottleSerializer, StoreSerializer, RegionSerializer,
    LabelAnalysisResponseSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q

class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "country"]
    ordering_fields = ["name", "country", "wine_count"]
    ordering = ["country", "name"]
    
    def get_queryset(self):
        return Region.objects.annotate(
            wine_count=Count('wines', distinct=True)
        )

class WineViewSet(viewsets.ModelViewSet):
    
    serializer_class = WineSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "country", "region__name", "grape_varieties", "wine_type"]
    ordering_fields = ["name", "vintage", "country", "bottle_count", "in_stock_count"]
    ordering = ["name"]
    def get_queryset(self):
        return (
                    Wine.objects.all()
                    .annotate(
                        bottle_count=Count("bottle", distinct=True),
                        in_stock_count=Count("bottle", filter=Q(bottle__consumed_at__isnull=True), distinct=True),
                )
            )

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser], url_path='analyze-label')
    def analyze_label(self, request):
        """
        Analyze a wine bottle label image and extract wine information.
        
        POST /api/wines/analyze-label/
        Content-Type: multipart/form-data
        Body: image (file)
        
        Returns extracted wine data with confidence scores and optional region matching.
        """
        from .services import analyze_wine_label, LabelAnalysisError
        
        # Validate image is provided
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image provided. Please upload an image file."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        try:
            result = analyze_wine_label(image_file)
            serializer = LabelAnalysisResponseSerializer(data=result)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except LabelAnalysisError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            # Log unexpected errors for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Unexpected error in analyze_label")
            return Response(
                {"error": "An unexpected error occurred while analyzing the image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BottleViewSet(viewsets.ModelViewSet):
    queryset = Bottle.objects.all().order_by('-id')
    serializer_class = BottleSerializer
    filter_backends = [DjangoFilterBackend]

    # Allow /api/bottles/?wine=1
    filterset_fields = ["wine"]
    @action(detail=True, methods=['post'])
    def consume(self, request, pk=None):
        bottle = self.get_object()
                # idempotent: if already consumed, just return current state
        if bottle.consumed_at is None:
            bottle.consumed_at = timezone.localdate()
            bottle.save(update_fields=["consumed_at"])

        return Response(self.get_serializer(bottle).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def undo_consume(self, request, pk=None):
        bottle = self.get_object()
              
        if bottle.consumed_at is not None:
            bottle.consumed_at = None
            bottle.save(update_fields=["consumed_at"])

        return Response(self.get_serializer(bottle).data, status=status.HTTP_200_OK)
class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all().order_by('-id')
    serializer_class = StoreSerializer